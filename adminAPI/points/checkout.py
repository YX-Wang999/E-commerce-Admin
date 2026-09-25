"""Checkout points deduction helpers."""

from __future__ import annotations

from decimal import Decimal, ROUND_DOWN

from customers.models import Customer
from points.models import PointsTransaction
from points.services import change_points, get_or_create_account, get_rule_decimal

POINTS_PER_YUAN = 100
MAX_POINTS_DEDUCT_RATIO = Decimal('0.30')
MIN_ORDER_FOR_REDEEM = Decimal('10')


def get_redeem_rule() -> tuple[int, Decimal, Decimal]:
    """Return (points_per_yuan, max_ratio, min_order_amount)."""
    points_per_yuan = int(get_rule_decimal('redeem_rate', POINTS_PER_YUAN))
    max_rate = get_rule_decimal('redeem_max_rate', Decimal('30'))
    max_ratio = (max_rate / Decimal('100')).quantize(Decimal('0.01'))
    min_amount = get_rule_decimal('redeem_min_amount', MIN_ORDER_FOR_REDEEM)
    return max(points_per_yuan, 1), max_ratio, min_amount


def points_to_yuan(points: int, points_per_yuan: int | None = None) -> Decimal:
    rate = points_per_yuan or get_redeem_rule()[0]
    return (Decimal(points) / Decimal(rate)).quantize(Decimal('0.01'), rounding=ROUND_DOWN)


def yuan_to_points(amount: Decimal, points_per_yuan: int | None = None) -> int:
    rate = points_per_yuan or get_redeem_rule()[0]
    return int((amount * Decimal(rate)).quantize(Decimal('1'), rounding=ROUND_DOWN))


def get_checkout_points_info(customer: Customer, order_amount: Decimal) -> dict:
    account = get_or_create_account(customer)
    points_per_yuan, max_ratio, min_amount = get_redeem_rule()
    eligible = order_amount >= min_amount
    max_deduct_amount = (
        (order_amount * max_ratio).quantize(Decimal('0.01'), rounding=ROUND_DOWN) if eligible else Decimal('0')
    )
    max_points_by_ratio = yuan_to_points(max_deduct_amount, points_per_yuan)
    max_usable_points = min(account.balance, max_points_by_ratio) if eligible else 0
    max_deduct_from_points = points_to_yuan(max_usable_points, points_per_yuan)
    if max_deduct_from_points > max_deduct_amount:
        max_deduct_from_points = max_deduct_amount
        max_usable_points = yuan_to_points(max_deduct_from_points, points_per_yuan)

    return {
        'balance': account.balance,
        'points_per_yuan': points_per_yuan,
        'max_deduct_ratio': str(max_ratio),
        'min_order_amount': str(min_amount),
        'eligible': eligible,
        'max_usable_points': max_usable_points,
        'max_deduct_amount': str(max_deduct_from_points),
        'order_amount': str(order_amount),
    }


def validate_points_deduction(
    customer: Customer,
    order_amount: Decimal,
    use_points: bool,
    points_amount: int | None,
) -> tuple[int, Decimal]:
    if not use_points or not points_amount or points_amount <= 0:
        return 0, Decimal('0')

    info = get_checkout_points_info(customer, order_amount)
    if not info['eligible']:
        raise ValueError(f'订单满 {info["min_order_amount"]} 元才可使用积分')

    max_points = info['max_usable_points']
    if points_amount > max_points:
        raise ValueError(f'最多可使用 {max_points} 积分')

    points_per_yuan = info['points_per_yuan']
    deduct = points_to_yuan(points_amount, points_per_yuan)
    max_deduct = Decimal(info['max_deduct_amount'])
    if deduct > max_deduct:
        deduct = max_deduct
        points_amount = yuan_to_points(deduct, points_per_yuan)

    if deduct > order_amount:
        deduct = order_amount
        points_amount = yuan_to_points(deduct, points_per_yuan)

    account = get_or_create_account(customer)
    if points_amount > account.balance:
        raise ValueError('积分余额不足')

    return points_amount, deduct


def spend_points_for_order(customer: Customer, order, points_amount: int) -> None:
    if points_amount <= 0:
        return
    change_points(
        customer,
        -points_amount,
        PointsTransaction.TYPE_SPEND_CHECKOUT,
        source=f'order:{order.id}',
        description=f'订单 {order.order_no} 积分抵扣',
    )


def refund_points_for_order(customer: Customer, order) -> None:
    if order.points_used <= 0:
        return
    source = f'order:{order.id}'
    from points.models import PointsTransaction

    if PointsTransaction.objects.filter(customer=customer, source=source, trans_type=PointsTransaction.TYPE_SPEND_CHECKOUT).exists():
        refund_source = f'order_refund:{order.id}'
        if not PointsTransaction.objects.filter(customer=customer, source=refund_source).exists():
            change_points(
                customer,
                order.points_used,
                PointsTransaction.TYPE_REFUND_ORDER,
                source=refund_source,
                description=f'订单 {order.order_no} 取消退还积分',
            )
