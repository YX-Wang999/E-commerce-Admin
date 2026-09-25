"""Seller points business logic."""

from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal, ROUND_DOWN

from django.db import transaction
from django.utils import timezone

from customers.models import Customer
from seller_points.limits import (
    DEFAULT_EARN_RATE,
    DEFAULT_EXPIRE_DAYS,
    DEFAULT_MAX_EARN_PER_ORDER,
    DEFAULT_MAX_REDEEM_PERCENT,
    DEFAULT_REDEEM_RATE,
    MAX_EARN_RATE,
    MAX_REDEEM_PERCENT,
    MAX_REDEEM_RATE,
    MIN_EXPIRE_DAYS,
    MIN_REDEEM_RATE,
)
from seller_points.models import SellerPointsAccount, SellerPointsRule, SellerPointsTransaction
from tenants.models import Tenant

logger = logging.getLogger(__name__)


def clamp_rule_values(data: dict) -> dict:
    """Apply platform limits to rule payload."""
    result = dict(data)
    if 'earn_rate' in result:
        rate = Decimal(str(result['earn_rate']))
        result['earn_rate'] = min(max(rate, Decimal('0')), MAX_EARN_RATE)
    if 'redeem_rate' in result:
        rate = Decimal(str(result['redeem_rate']))
        result['redeem_rate'] = min(max(rate, MIN_REDEEM_RATE), MAX_REDEEM_RATE)
    if 'max_redeem_rate' in result:
        pct = Decimal(str(result['max_redeem_rate']))
        result['max_redeem_rate'] = min(max(pct, Decimal('0')), MAX_REDEEM_PERCENT)
    if 'expire_days' in result:
        days = int(result['expire_days'])
        result['expire_days'] = max(days, MIN_EXPIRE_DAYS)
    if 'max_earn_per_order' in result:
        result['max_earn_per_order'] = max(int(result['max_earn_per_order']), 0)
    return result


def get_or_create_rule(tenant: Tenant) -> SellerPointsRule:
    rule, _ = SellerPointsRule.objects.get_or_create(
        tenant=tenant,
        defaults={
            'earn_rate': DEFAULT_EARN_RATE,
            'redeem_rate': DEFAULT_REDEEM_RATE,
            'max_redeem_rate': DEFAULT_MAX_REDEEM_PERCENT,
            'expire_days': DEFAULT_EXPIRE_DAYS,
            'max_earn_per_order': DEFAULT_MAX_EARN_PER_ORDER,
        },
    )
    return rule


def get_or_create_account(tenant: Tenant, customer: Customer) -> SellerPointsAccount:
    rule = get_or_create_rule(tenant)
    expire_at = timezone.now() + timedelta(days=rule.expire_days)
    account, created = SellerPointsAccount.objects.get_or_create(
        tenant=tenant,
        customer=customer,
        defaults={'expire_at': expire_at},
    )
    if not created and account.expire_at is None:
        account.expire_at = expire_at
        account.save(update_fields=['expire_at', 'updated_at'])
    return account


def _refresh_expire_at(account: SellerPointsAccount, rule: SellerPointsRule) -> None:
    account.expire_at = timezone.now() + timedelta(days=rule.expire_days)
    account.save(update_fields=['expire_at', 'updated_at'])


def _has_source(tenant: Tenant, customer: Customer, source_id: str, trans_type: str) -> bool:
    return SellerPointsTransaction.objects.filter(
        tenant=tenant,
        customer=customer,
        source_id=source_id,
        trans_type=trans_type,
    ).exists()


@transaction.atomic
def change_seller_points(
    tenant: Tenant,
    customer: Customer,
    amount: int,
    trans_type: str,
    *,
    source_id: str = '',
    description: str = '',
) -> SellerPointsTransaction:
    if amount == 0:
        raise ValueError('积分变动不能为 0')
    rule = get_or_create_rule(tenant)
    if not rule.is_active and trans_type not in (
        SellerPointsTransaction.TYPE_ADMIN_ADJUST,
        SellerPointsTransaction.TYPE_REFUND_ORDER,
    ):
        raise ValueError('商家积分未启用')

    account = get_or_create_account(tenant, customer)
    account = SellerPointsAccount.objects.select_for_update().get(pk=account.pk)
    new_balance = account.balance + amount
    if new_balance < 0:
        raise ValueError('店铺积分余额不足')

    if amount > 0 and trans_type != SellerPointsTransaction.TYPE_REFUND_ORDER:
        account.total_earned += amount
        _refresh_expire_at(account, rule)
    elif amount < 0 and trans_type != SellerPointsTransaction.TYPE_REFUND_ORDER:
        account.total_spent += abs(amount)

    account.balance = new_balance
    account.save(update_fields=['balance', 'total_earned', 'total_spent', 'expire_at', 'updated_at'])

    return SellerPointsTransaction.objects.create(
        tenant=tenant,
        customer=customer,
        account=account,
        amount=amount,
        balance_after=new_balance,
        trans_type=trans_type,
        source_id=source_id,
        description=description,
    )


def calculate_earn_points(tenant: Tenant, order_amount: Decimal) -> int:
    rule = get_or_create_rule(tenant)
    if not rule.is_active:
        return 0
    points = int((order_amount * rule.earn_rate).quantize(Decimal('1'), rounding=ROUND_DOWN))
    if rule.max_earn_per_order:
        points = min(points, rule.max_earn_per_order)
    return max(points, 0)


def award_order_seller_points(order) -> SellerPointsTransaction | None:
    if not order.customer_id or not order.tenant_id:
        return None
    source_id = f'order:{order.id}'
    if _has_source(order.tenant, order.customer, source_id, SellerPointsTransaction.TYPE_EARN_ORDER):
        return None
    points = calculate_earn_points(order.tenant, Decimal(order.total_amount))
    if points <= 0:
        return None
    return change_seller_points(
        order.tenant,
        order.customer,
        points,
        SellerPointsTransaction.TYPE_EARN_ORDER,
        source_id=source_id,
        description=f'订单 {order.order_no} 完成奖励',
    )


def refund_seller_points_for_order(order) -> None:
    if not order.customer_id or not order.tenant_id or order.seller_points_used <= 0:
        return
    source_id = f'order:{order.id}'
    refund_source = f'order_refund:{order.id}'
    if not _has_source(order.tenant, order.customer, source_id, SellerPointsTransaction.TYPE_REDEEM_ORDER):
        return
    if _has_source(order.tenant, order.customer, refund_source, SellerPointsTransaction.TYPE_REFUND_ORDER):
        return
    change_seller_points(
        order.tenant,
        order.customer,
        order.seller_points_used,
        SellerPointsTransaction.TYPE_REFUND_ORDER,
        source_id=refund_source,
        description=f'订单 {order.order_no} 取消退还店铺积分',
    )
