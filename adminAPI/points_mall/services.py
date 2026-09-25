"""Points mall business logic."""

from __future__ import annotations

import secrets
import string
from datetime import timedelta

from django.db import transaction
from django.db.models import F, Q, Sum
from django.utils import timezone

from customers.models import Customer
from points.models import PointsTransaction
from points.services import change_points, get_or_create_account
from points_mall.models import PointsMallItem, PointsMallOrder


class ExchangeError(Exception):
    pass


def _generate_order_no() -> str:
    ts = timezone.now().strftime('%Y%m%d%H%M%S')
    suffix = ''.join(secrets.choice(string.digits) for _ in range(4))
    return f'PM{ts}{suffix}'


def _generate_coupon_code() -> str:
    return 'PM' + secrets.token_hex(4).upper()


def _item_queryset(
    *,
    item_type: str | None = None,
    category: str | None = None,
    keyword: str | None = None,
    sort: str | None = None,
):
    now = timezone.now()
    qs = PointsMallItem.objects.filter(status=PointsMallItem.STATUS_ON_SALE)
    qs = qs.filter(Q(start_at__isnull=True) | Q(start_at__lte=now))
    qs = qs.filter(Q(end_at__isnull=True) | Q(end_at__gte=now))

    resolved_type = category or item_type
    if resolved_type and resolved_type not in {'all', ''}:
        type_map = {
            'product': PointsMallItem.TYPE_PHYSICAL,
            'physical': PointsMallItem.TYPE_PHYSICAL,
            'coupon': PointsMallItem.TYPE_COUPON,
            'vip': PointsMallItem.TYPE_BENEFIT,
            'benefit': PointsMallItem.TYPE_BENEFIT,
            'lottery': PointsMallItem.TYPE_LOTTERY,
        }
        mapped = type_map.get(resolved_type, resolved_type)
        qs = qs.filter(item_type=mapped)

    if keyword:
        qs = qs.filter(name__icontains=keyword)

    sort_key = (sort or 'default').strip().lower()
    if sort_key == 'hot':
        qs = qs.filter(is_hot=True).order_by('-exchanged_count', 'sort_order', '-id')
    elif sort_key == 'new':
        since = now - timedelta(days=7)
        qs = qs.filter(created_at__gte=since).order_by('-created_at', 'sort_order', '-id')
    elif sort_key == 'ending':
        qs = qs.filter(end_at__isnull=False, end_at__gte=now).order_by('end_at', 'sort_order', '-id')
    else:
        qs = qs.order_by('sort_order', '-id')
    return qs


def list_items(
    *,
    item_type: str | None = None,
    category: str | None = None,
    keyword: str | None = None,
    sort: str | None = None,
):
    return _item_queryset(item_type=item_type, category=category, keyword=keyword, sort=sort)


def get_item(item_id: int) -> PointsMallItem:
    item = _item_queryset().filter(pk=item_id).first()
    if item is None:
        raise ExchangeError('商品不存在或已下架')
    return item


def _validate_address(address: dict | None, item: PointsMallItem) -> dict:
    needs_address = item.requires_address or item.item_type == PointsMallItem.TYPE_PHYSICAL
    if not needs_address:
        return address or {}
    if not address:
        raise ExchangeError('请填写收货地址')
    required = ('name', 'phone', 'province', 'city', 'district', 'detail')
    for key in required:
        if not str(address.get(key) or '').strip():
            raise ExchangeError('收货地址不完整')
    return address


@transaction.atomic
def exchange_item(
    customer: Customer,
    item_id: int,
    *,
    quantity: int = 1,
    address: dict | None = None,
) -> PointsMallOrder:
    if quantity < 1:
        raise ExchangeError('数量无效')

    item = PointsMallItem.objects.select_for_update().filter(pk=item_id).first()
    if item is None or item.status != PointsMallItem.STATUS_ON_SALE:
        raise ExchangeError('商品不存在或已下架')

    now = timezone.now()
    if item.start_at and item.start_at > now:
        raise ExchangeError('商品尚未开始兑换')
    if item.end_at and item.end_at < now:
        raise ExchangeError('商品已结束兑换')
    if item.stock < quantity:
        raise ExchangeError('库存不足')

    points_needed = item.points_required * quantity
    account = get_or_create_account(customer)
    if account.balance < points_needed:
        raise ExchangeError('积分不足')

    already = PointsMallOrder.objects.filter(
        customer=customer,
        item=item,
    ).exclude(status=PointsMallOrder.STATUS_CANCELLED).aggregate(total=Sum('quantity'))['total'] or 0
    if already + quantity > item.per_user_limit:
        raise ExchangeError('超过限购数量')

    address_data = _validate_address(address, item)

    change_points(
        customer,
        -points_needed,
        PointsTransaction.TYPE_SPEND_REDEEM,
        source=f'points_mall:{item.id}',
        description=f'兑换 {item.name} x{quantity}',
    )

    item.stock = F('stock') - quantity
    item.exchanged_count = F('exchanged_count') + quantity
    item.save(update_fields=['stock', 'exchanged_count', 'updated_at'])
    item.refresh_from_db()

    coupon_code = ''
    if item.item_type == PointsMallItem.TYPE_COUPON:
        coupon_code = _generate_coupon_code()

    order = PointsMallOrder.objects.create(
        order_no=_generate_order_no(),
        customer=customer,
        item=item,
        item_name=item.name,
        item_type=item.item_type,
        points_spent=points_needed,
        quantity=quantity,
        address=address_data,
        status=PointsMallOrder.STATUS_PENDING,
        coupon_code=coupon_code,
    )

    if item.item_type in {PointsMallItem.TYPE_COUPON, PointsMallItem.TYPE_BENEFIT, PointsMallItem.TYPE_LOTTERY}:
        order.status = PointsMallOrder.STATUS_COMPLETED
        order.save(update_fields=['status', 'updated_at'])

    try:
        from notification.services import notify_points_mall_exchanged

        notify_points_mall_exchanged(order=order)
    except Exception:
        pass

    return order


@transaction.atomic
def ship_order(order_id: int, *, logistics_company: str, logistics_no: str, remark: str = '') -> PointsMallOrder:
    order = PointsMallOrder.objects.select_for_update().filter(pk=order_id).first()
    if order is None:
        raise ExchangeError('订单不存在')
    if order.status in {PointsMallOrder.STATUS_SHIPPED, PointsMallOrder.STATUS_COMPLETED, PointsMallOrder.STATUS_CANCELLED}:
        raise ExchangeError('当前状态不可发货')
    order.status = PointsMallOrder.STATUS_SHIPPED
    order.logistics_company = logistics_company.strip()
    order.logistics_no = logistics_no.strip()
    order.remark = remark.strip()
    order.shipped_at = timezone.now()
    order.save(update_fields=['status', 'logistics_company', 'logistics_no', 'remark', 'shipped_at', 'updated_at'])

    try:
        from notification.services import notify_points_mall_shipped

        notify_points_mall_shipped(order=order)
    except Exception:
        pass
    return order


def mall_stats() -> dict:
    orders = PointsMallOrder.objects.exclude(status=PointsMallOrder.STATUS_CANCELLED)
    return {
        'order_count': orders.count(),
        'points_spent': int(orders.aggregate(total=Sum('points_spent'))['total'] or 0),
        'item_count': PointsMallItem.objects.filter(status=PointsMallItem.STATUS_ON_SALE).count(),
    }


def hot_items(limit: int = 10):
    return _item_queryset().filter(is_hot=True).order_by('-exchanged_count')[:limit]
