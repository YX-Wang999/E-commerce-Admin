"""Promotion checkout and mall-facing business logic."""

from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal, ROUND_DOWN
from typing import Iterable

from django.db import transaction
from django.utils import timezone

from customers.models import Customer
from products.models import Product
from promotion.models import (
    Coupon,
    GroupBuyActivity,
    GroupOrder,
    SeckillActivity,
    UserCoupon,
)

POINTS_PER_YUAN = 100
MAX_POINTS_DEDUCT_RATIO = Decimal('0.30')


def _money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal('0.01'))


def _running_seckill_qs():
    now = timezone.now()
    return SeckillActivity.objects.filter(
        status=SeckillActivity.STATUS_RUNNING,
        start_time__lte=now,
        end_time__gte=now,
    )


def _running_groupbuy_qs():
    now = timezone.now()
    return GroupBuyActivity.objects.filter(
        status=GroupBuyActivity.STATUS_RUNNING,
        start_time__lte=now,
        end_time__gte=now,
    )


def get_seckill_for_product(product_id: int) -> SeckillActivity | None:
    return (
        _running_seckill_qs()
        .filter(products__id=product_id)
        .order_by('-start_time')
        .first()
    )


def get_groupbuy_for_product(product_id: int) -> GroupBuyActivity | None:
    return (
        _running_groupbuy_qs()
        .filter(product_id=product_id)
        .order_by('-start_time')
        .first()
    )


def coupon_applicable_to_line(coupon: Coupon, product: Product, line_total: Decimal) -> bool:
    if line_total < Decimal(str(coupon.min_amount or 0)):
        return False
    if coupon.applicable_scope == Coupon.SCOPE_ALL:
        return True
    if coupon.applicable_scope == Coupon.SCOPE_CATEGORY:
        return coupon.applicable_category_id == product.category_id
    if coupon.applicable_scope == Coupon.SCOPE_PRODUCT:
        return coupon.applicable_products.filter(pk=product.id).exists()
    return False


def calculate_coupon_discount(coupon: Coupon, subtotal: Decimal, products: Iterable[tuple[Product, int]]) -> Decimal:
    """Return discount amount for coupon against cart lines."""
    eligible_total = Decimal('0')
    for product, qty in products:
        line_total = Decimal(str(product.price)) * qty
        if coupon_applicable_to_line(coupon, product, line_total):
            eligible_total += line_total

    if eligible_total <= 0:
        return Decimal('0')

    if coupon.coupon_type == Coupon.TYPE_FIXED:
        return min(_money(coupon.discount_amount or 0), eligible_total)
    if coupon.coupon_type == Coupon.TYPE_FREE:
        return min(_money(coupon.discount_amount or 0), eligible_total)
    if coupon.coupon_type == Coupon.TYPE_DISCOUNT:
        rate = Decimal(str(coupon.discount_rate or 0))
        if rate <= 0:
            return Decimal('0')
        if rate > 1:
            rate = rate / Decimal('100')
        discount = _money(eligible_total * (Decimal('1') - rate))
        max_discount = coupon.max_discount
        if max_discount is not None:
            discount = min(discount, _money(max_discount))
        return min(discount, eligible_total)
    return Decimal('0')


def get_customer_user_coupon(customer: Customer, user_coupon_id: int) -> UserCoupon | None:
    return (
        UserCoupon.objects.select_related('coupon')
        .filter(pk=user_coupon_id, customer=customer, status=UserCoupon.STATUS_UNUSED)
        .first()
    )


def list_available_coupons(
    customer: Customer,
    products: list[tuple[Product, int]],
    subtotal: Decimal,
) -> list[dict]:
    now = timezone.now()
    qs = UserCoupon.objects.select_related('coupon').filter(
        customer=customer,
        status=UserCoupon.STATUS_UNUSED,
        expired_at__gt=now,
        coupon__status=Coupon.STATUS_PUBLISHED,
    )
    results = []
    for uc in qs:
        discount = calculate_coupon_discount(uc.coupon, subtotal, products)
        results.append({
            'id': uc.id,
            'code': uc.code,
            'coupon_id': uc.coupon_id,
            'name': uc.coupon.name,
            'coupon_type': uc.coupon.coupon_type,
            'min_amount': str(uc.coupon.min_amount),
            'discount_amount': str(uc.coupon.discount_amount or ''),
            'discount_rate': str(uc.coupon.discount_rate or ''),
            'expired_at': uc.expired_at.isoformat(),
            'available': discount > 0,
            'estimated_discount': str(discount),
        })
    return results


def validate_user_coupon(customer: Customer, user_coupon_id: int, products, subtotal: Decimal) -> tuple[UserCoupon, Decimal]:
    uc = get_customer_user_coupon(customer, user_coupon_id)
    if uc is None:
        raise ValueError('优惠券不可用')
    if uc.expired_at <= timezone.now():
        raise ValueError('优惠券已过期')
    discount = calculate_coupon_discount(uc.coupon, subtotal, products)
    if discount <= 0:
        raise ValueError('当前订单不满足优惠券使用条件')
    return uc, discount


@transaction.atomic
def lock_user_coupon(user_coupon: UserCoupon, order) -> None:
    locked = UserCoupon.objects.select_for_update().get(pk=user_coupon.pk)
    if locked.status != UserCoupon.STATUS_UNUSED:
        raise ValueError('优惠券已被使用')
    locked.status = UserCoupon.STATUS_USED
    locked.used_at = timezone.now()
    locked.order = order
    locked.save(update_fields=['status', 'used_at', 'order'])


@transaction.atomic
def release_user_coupon_for_order(order) -> None:
    if not order.user_coupon_id:
        return
    locked = UserCoupon.objects.select_for_update().filter(pk=order.user_coupon_id).first()
    if locked is None or locked.status != UserCoupon.STATUS_USED or locked.order_id != order.id:
        return
    locked.status = UserCoupon.STATUS_UNUSED
    locked.used_at = None
    locked.order = None
    locked.save(update_fields=['status', 'used_at', 'order'])


def generate_user_coupon_code() -> str:
    return uuid.uuid4().hex[:16].upper()


@transaction.atomic
def receive_coupon(customer: Customer, coupon_id: int) -> UserCoupon:
    coupon = Coupon.objects.select_for_update().get(pk=coupon_id)
    if coupon.status != Coupon.STATUS_PUBLISHED:
        raise ValueError('优惠券不可领取')
    received_count = UserCoupon.objects.filter(coupon=coupon, customer=customer).count()
    if received_count >= coupon.per_user_limit:
        raise ValueError('已达到领取上限')
    total_received = UserCoupon.objects.filter(coupon=coupon).count()
    if total_received >= coupon.total_quantity:
        raise ValueError('优惠券已领完')

    if coupon.valid_type == Coupon.VALID_FIXED:
        expired_at = coupon.valid_end
    else:
        days = coupon.valid_days or 7
        expired_at = timezone.now() + timedelta(days=days)

    return UserCoupon.objects.create(
        coupon=coupon,
        customer=customer,
        code=generate_user_coupon_code(),
        expired_at=expired_at,
    )


def seckill_sold_count(activity_id: int) -> int:
    from django.db.models import Sum

    from orders.models import Order, OrderItem

    return (
        OrderItem.objects.filter(
            order__promotion_type='seckill',
            order__promotion_ref=str(activity_id),
        )
        .exclude(order__status=Order.STATUS_CANCELLED)
        .aggregate(total=Sum('quantity'))['total']
        or 0
    )


def seckill_progress(activity: SeckillActivity) -> dict:
    sold = seckill_sold_count(activity.id)
    remaining = max(0, activity.seckill_stock)
    total = sold + remaining
    pct = int(min(100, max(0, (sold / total) * 100))) if total > 0 else 0
    return {
        'remaining_stock': remaining,
        'sold_count': sold,
        'total_stock': total,
        'sold_percent': pct,
    }


def groupbuy_progress(activity: GroupBuyActivity) -> dict:
    pending_orders = GroupOrder.objects.filter(
        activity=activity,
        status=GroupOrder.STATUS_PENDING,
    )
    pending_groups = pending_orders.count()
    current_group_members = pending_groups or 0
    need_more = max(0, activity.group_size - current_group_members)
    progress_percent = 0
    if activity.group_size > 0:
        progress_percent = int(
            min(100, max(0, (current_group_members / activity.group_size) * 100)),
        )
    open_group = pending_orders.order_by('created_at').first()
    return {
        'pending_groups': pending_groups,
        'joined_count': current_group_members,
        'current_group_members': current_group_members,
        'need_more': need_more,
        'progress_percent': progress_percent,
        'open_group_order_id': open_group.id if open_group else None,
    }
