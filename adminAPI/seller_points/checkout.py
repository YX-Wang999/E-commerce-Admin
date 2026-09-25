"""Checkout integration for seller (shop) points."""

from __future__ import annotations

from decimal import Decimal, ROUND_DOWN

from customers.models import Customer
from seller_points.models import SellerPointsTransaction
from seller_points.services import change_seller_points, get_or_create_account, get_or_create_rule
from tenants.models import Tenant


def points_to_yuan(points: int, redeem_rate: Decimal) -> Decimal:
    return (Decimal(points) / redeem_rate).quantize(Decimal('0.01'), rounding=ROUND_DOWN)


def yuan_to_points(amount: Decimal, redeem_rate: Decimal) -> int:
    return int((amount * redeem_rate).quantize(Decimal('1'), rounding=ROUND_DOWN))


def get_checkout_seller_points_info(customer: Customer, tenant: Tenant, order_amount: Decimal) -> dict:
    rule = get_or_create_rule(tenant)
    account = get_or_create_account(tenant, customer)
    redeem_rate = Decimal(rule.redeem_rate)
    max_ratio = Decimal(rule.max_redeem_rate) / Decimal('100')
    max_deduct_amount = (order_amount * max_ratio).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
    max_points_by_ratio = yuan_to_points(max_deduct_amount, redeem_rate)
    max_usable_points = min(account.balance, max_points_by_ratio)
    max_deduct_from_points = points_to_yuan(max_usable_points, redeem_rate)
    if max_deduct_from_points > max_deduct_amount:
        max_deduct_from_points = max_deduct_amount
        max_usable_points = yuan_to_points(max_deduct_from_points, redeem_rate)

    return {
        'enabled': rule.is_active,
        'points_name': rule.points_name,
        'balance': account.balance,
        'redeem_rate': str(redeem_rate),
        'max_redeem_percent': str(rule.max_redeem_rate),
        'max_usable_points': max_usable_points,
        'max_deduct_amount': str(max_deduct_from_points),
        'order_amount': str(order_amount),
        'expire_at': account.expire_at.isoformat() if account.expire_at else None,
    }


def validate_seller_points_deduction(
    customer: Customer,
    tenant: Tenant,
    order_amount: Decimal,
    use_seller_points: bool,
    seller_points_amount: int | None,
) -> tuple[int, Decimal]:
    if not use_seller_points or not seller_points_amount or seller_points_amount <= 0:
        return 0, Decimal('0')

    rule = get_or_create_rule(tenant)
    if not rule.is_active:
        raise ValueError('该店铺积分未启用')

    info = get_checkout_seller_points_info(customer, tenant, order_amount)
    max_points = info['max_usable_points']
    if seller_points_amount > max_points:
        raise ValueError(f'最多可使用 {max_points} {rule.points_name}')

    redeem_rate = Decimal(info['redeem_rate'])
    deduct = points_to_yuan(seller_points_amount, redeem_rate)
    max_deduct = Decimal(info['max_deduct_amount'])
    if deduct > max_deduct:
        deduct = max_deduct
        seller_points_amount = yuan_to_points(deduct, redeem_rate)
    if deduct > order_amount:
        deduct = order_amount
        seller_points_amount = yuan_to_points(deduct, redeem_rate)

    account = get_or_create_account(tenant, customer)
    if seller_points_amount > account.balance:
        raise ValueError(f'{rule.points_name}余额不足')

    return seller_points_amount, deduct


def spend_seller_points_for_order(customer: Customer, tenant: Tenant, order, points_amount: int) -> None:
    if points_amount <= 0:
        return
    rule = get_or_create_rule(tenant)
    change_seller_points(
        tenant,
        customer,
        -points_amount,
        SellerPointsTransaction.TYPE_REDEEM_ORDER,
        source_id=f'order:{order.id}',
        description=f'订单 {order.order_no} {rule.points_name}抵扣',
    )
