"""Points business logic."""

from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal, ROUND_DOWN

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from customers.models import Customer
from orders.models import Order
from points.models import PointsAccount, PointsRule, PointsSignInRecord, PointsTransaction

logger = logging.getLogger(__name__)

DAILY_POINTS_LIMIT = 100
MONTHLY_POINTS_LIMIT = 500
ORDER_POINTS_LIMIT = 500
REVIEW_POINTS_LIMIT = 20
POINTS_EXPIRE_DAYS = 365


def get_active_rule(code: str) -> PointsRule | None:
    return PointsRule.objects.filter(code=code, is_active=True).first()


def get_rule_decimal(code: str, default=0) -> Decimal:
    rule = get_active_rule(code)
    if not rule:
        return Decimal(str(default))
    return Decimal(str(rule.current_value or default))


def get_rule_int(code: str, default: int = 0) -> int:
    return int(get_rule_decimal(code, default))


def points_to_yuan(points: int) -> Decimal:
    rate = get_rule_decimal('redeem_rate', Decimal('10'))
    if rate <= 0:
        return Decimal('0')
    return (Decimal(points) / rate).quantize(Decimal('0.01'))


def _earned_since(customer: Customer, since) -> int:
    from django.db.models import Sum

    total = PointsTransaction.objects.filter(
        customer=customer,
        amount__gt=0,
        created_at__gte=since,
    ).aggregate(total=Sum('amount'))['total']
    return int(total or 0)


def _cap_positive_earn(customer: Customer, amount: int) -> int:
    if amount <= 0:
        return amount
    now = timezone.now()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = day_start.replace(day=1)
    daily_left = max(DAILY_POINTS_LIMIT - _earned_since(customer, day_start), 0)
    monthly_left = max(MONTHLY_POINTS_LIMIT - _earned_since(customer, month_start), 0)
    return max(0, min(amount, daily_left, monthly_left))


def _touch_expire_at(account: PointsAccount) -> None:
    expire_at = timezone.now() + timedelta(days=POINTS_EXPIRE_DAYS)
    if account.balance_expire_at is None or account.balance_expire_at < timezone.now():
        account.balance_expire_at = expire_at
    else:
        account.balance_expire_at = max(account.balance_expire_at, expire_at)
    account.save(update_fields=['balance_expire_at', 'updated_at'])


def _has_source_transaction(customer: Customer, source: str) -> bool:
    return PointsTransaction.objects.filter(customer=customer, source=source).exists()


def _award_once(
    customer: Customer,
    code: str,
    source: str,
    description: str,
    *,
    trans_type: str = PointsTransaction.TYPE_EARN_ORDER,
    multiplier: Decimal = Decimal('1'),
) -> PointsTransaction | None:
    if _has_source_transaction(customer, source):
        return None
    rule = get_active_rule(code)
    if not rule:
        return None
    base = Decimal(str(rule.current_value or 0))
    if base <= 0:
        return None
    points = int((base * multiplier).quantize(Decimal('1'), rounding=ROUND_DOWN))
    if points <= 0:
        return None
    return change_points(customer, points, trans_type, source=source, description=description)


def get_or_create_account(customer: Customer, tenant=None) -> PointsAccount:
    if tenant is None:
        from tenants.context import get_current_tenant

        tenant = get_current_tenant() or getattr(customer, 'tenant', None)
    account, created = PointsAccount.objects.get_or_create(
        customer=customer,
        tenant=tenant,
        defaults={'balance': customer.points, 'total_earned': customer.points, 'total_spent': 0},
    )
    if created and customer.points:
        customer.points = account.balance
        customer.save(update_fields=['points', 'updated_at'])
    return account


def _sync_customer_points(customer: Customer, balance: int) -> None:
    if customer.points != balance:
        customer.points = balance
        customer.save(update_fields=['points', 'updated_at'])


def _counts_toward_stats(trans_type: str) -> bool:
    return trans_type != PointsTransaction.TYPE_REFUND_ORDER


@transaction.atomic
def change_points(
    customer: Customer,
    amount: int,
    trans_type: str,
    *,
    source: str = '',
    description: str = '',
) -> PointsTransaction:
    if amount == 0:
        raise ValueError('积分变动不能为 0')
    if amount > 0 and trans_type != PointsTransaction.TYPE_ADJUST_ADMIN:
        amount = _cap_positive_earn(customer, amount)
        if amount <= 0:
            raise ValueError('已达到今日或本月积分获取上限')
    account = get_or_create_account(customer)
    account = PointsAccount.objects.select_for_update().get(pk=account.pk)
    new_balance = account.balance + amount
    if new_balance < 0:
        raise ValueError('积分余额不足')

    if _counts_toward_stats(trans_type):
        if amount > 0:
            account.total_earned += amount
        else:
            account.total_spent += abs(amount)
    account.balance = new_balance
    account.save(update_fields=['balance', 'total_earned', 'total_spent', 'updated_at'])
    if amount > 0:
        _touch_expire_at(account)
    _sync_customer_points(customer, new_balance)

    return PointsTransaction.objects.create(
        customer=customer,
        amount=amount,
        balance_after=new_balance,
        trans_type=trans_type,
        source=source,
        description=description,
    )


def _calculate_order_base_points(order) -> int:
    rate = get_rule_decimal('order_rate', Decimal('1'))
    if rate <= 0:
        return 0
    base = int((Decimal(order.total_amount) * rate).quantize(Decimal('1'), rounding=ROUND_DOWN))
    try:
        from membership.services import get_or_create_profile

        profile = get_or_create_profile(order.customer)
        multiplier = profile.current_level.points_multiplier if profile.current_level else Decimal('1.00')
        return int((Decimal(base) * multiplier).quantize(Decimal('1'), rounding=ROUND_DOWN))
    except Exception:
        return base


def award_order_points(order) -> PointsTransaction | None:
    if not order.customer_id:
        return None
    source = f'order:{order.id}'
    if _has_source_transaction(order.customer, source):
        return None

    points = _calculate_order_base_points(order)
    bonus = get_rule_int('order_bonus', 0)
    points += bonus

    completed_before = (
        Order.objects.filter(customer=order.customer, status=Order.STATUS_COMPLETED)
        .exclude(pk=order.pk)
        .exists()
    )
    if not completed_before:
        points += get_rule_int('first_order', 0)

    if points <= 0:
        return None
    points = min(points, ORDER_POINTS_LIMIT)
    return change_points(
        order.customer,
        points,
        PointsTransaction.TYPE_EARN_ORDER,
        source=source,
        description=f'订单 {order.order_no} 完成奖励',
    )


def award_review_points(review) -> list[PointsTransaction]:
    txns: list[PointsTransaction] = []
    earned = 0

    def _award_limited(code, source, desc, *, trans_type=PointsTransaction.TYPE_EARN_REVIEW):
        nonlocal earned
        if earned >= REVIEW_POINTS_LIMIT:
            return None
        txn = _award_once(review.customer, code, source, desc, trans_type=trans_type)
        if txn:
            earned += txn.amount
            txns.append(txn)
        return txn

    _award_limited(
        'review',
        f'review:{review.id}',
        f'评价商品 {review.product.name}',
    )

    content = (review.content or '').lower()
    if any(token in content for token in ('.jpg', '.png', '.jpeg', 'img', '图片')):
        _award_limited(
            'review_photo',
            f'review_photo:{review.id}',
            f'带图评价 {review.product.name}',
        )

    if any(token in content for token in ('.mp4', 'video', '视频')):
        _award_limited(
            'review_video',
            f'review_video:{review.id}',
            f'带视频评价 {review.product.name}',
        )

    if not PointsTransaction.objects.filter(
        customer=review.customer,
        trans_type=PointsTransaction.TYPE_EARN_REVIEW,
        source__startswith='first_review:',
    ).exists():
        first = _award_limited(
            'first_review',
            f'first_review:{review.customer_id}',
            '首次评价奖励',
        )

    return txns


def award_profile_complete(customer: Customer) -> PointsTransaction | None:
    if not customer.name or not customer.phone:
        return None
    return _award_once(
        customer,
        'profile_complete',
        f'profile_complete:{customer.id}',
        '完善资料奖励',
        trans_type=PointsTransaction.TYPE_EARN_SIGN_IN,
    )


def award_bind_phone(customer: Customer) -> PointsTransaction | None:
    if not customer.phone:
        return None
    return _award_once(
        customer,
        'bind_phone',
        f'bind_phone:{customer.id}',
        '绑定手机奖励',
        trans_type=PointsTransaction.TYPE_EARN_SIGN_IN,
    )


def award_bind_email(customer: Customer) -> PointsTransaction | None:
    if not customer.email:
        return None
    return _award_once(
        customer,
        'bind_email',
        f'bind_email:{customer.id}',
        '绑定邮箱奖励',
        trans_type=PointsTransaction.TYPE_EARN_SIGN_IN,
    )


def award_share_product(customer: Customer, product_id: int) -> PointsTransaction | None:
    today = timezone.localdate().isoformat()
    return _award_once(
        customer,
        'share',
        f'share:{today}:{product_id}:{customer.id}',
        '分享商品奖励',
        trans_type=PointsTransaction.TYPE_EARN_SIGN_IN,
    )


@transaction.atomic
def sign_in(customer: Customer) -> dict:
    today = timezone.localdate()
    if PointsSignInRecord.objects.filter(customer=customer, sign_date=today).exists():
        raise ValueError('今日已签到')

    base_points = get_rule_int('sign_in', 0)
    if base_points <= 0:
        raise ValueError('签到规则未启用')

    yesterday = today - timedelta(days=1)
    yesterday_record = PointsSignInRecord.objects.filter(customer=customer, sign_date=yesterday).first()
    consecutive_days = (yesterday_record.consecutive_days + 1) if yesterday_record else 1

    streak_rule = get_active_rule('sign_in_streak')
    streak_unit = int(streak_rule.current_value) if streak_rule and streak_rule.current_value else base_points
    points = base_points + streak_unit * max(consecutive_days - 1, 0)

    birthday = getattr(customer, 'birthday', None)
    if birthday and birthday.month == today.month and birthday.day == today.day:
        points += get_rule_int('birthday', 0)

    txn = change_points(
        customer,
        points,
        PointsTransaction.TYPE_EARN_SIGN_IN,
        source=f'sign_in:{today.isoformat()}',
        description=f'每日签到（连续 {consecutive_days} 天）',
    )
    PointsSignInRecord.objects.create(
        customer=customer,
        sign_date=today,
        consecutive_days=consecutive_days,
        points_earned=points,
    )
    account = get_or_create_account(customer)
    return {
        'points_earned': points,
        'consecutive_days': consecutive_days,
        'balance': account.balance,
        'transaction': txn,
    }


def get_profile(customer: Customer) -> dict:
    account = get_or_create_account(customer)
    today = timezone.localdate()
    signed_today = PointsSignInRecord.objects.filter(customer=customer, sign_date=today).exists()
    last_record = PointsSignInRecord.objects.filter(customer=customer).order_by('-sign_date').first()
    total_earned, total_spent = _display_stats(customer)
    yuan_value = points_to_yuan(account.balance)
    return {
        'customer_id': customer.id,
        'customer_name': customer.name,
        'balance': account.balance,
        'balance_yuan': str(yuan_value),
        'balance_yuan_display': f'≈ ¥{yuan_value}',
        'total_earned': total_earned,
        'total_spent': total_spent,
        'signed_today': signed_today,
        'consecutive_days': last_record.consecutive_days if last_record else 0,
        'balance_expire_at': account.balance_expire_at.isoformat() if account.balance_expire_at else None,
    }


def _display_stats(customer: Customer) -> tuple[int, int]:
    from django.db.models import Sum

    refund_filter = Q(trans_type=PointsTransaction.TYPE_REFUND_ORDER) | Q(
        trans_type=PointsTransaction.TYPE_ADJUST_ADMIN,
        source__startswith='order_refund:',
    )
    qs = PointsTransaction.objects.filter(customer=customer)
    earned = qs.filter(amount__gt=0).exclude(refund_filter).aggregate(total=Sum('amount'))['total'] or 0
    spent = abs(qs.filter(amount__lt=0).aggregate(total=Sum('amount'))['total'] or 0)
    return int(earned), int(spent)
