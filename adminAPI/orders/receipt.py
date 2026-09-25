"""Order receipt confirmation logic."""

from __future__ import annotations

import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from logistics.models import Logistics
from orders.models import Order

logger = logging.getLogger(__name__)

RECEIPT_AUTO_CONFIRM_DAYS = 15
RECEIPT_TYPE_NORMAL = 'normal'
RECEIPT_TYPE_EARLY = 'early'
RECEIPT_TYPE_AUTO = 'auto'

EARLY_RECEIPT_CODE = 40901


class LogisticsNotDeliveredError(Exception):
    """Logistics has not reached delivered/signed state."""


def is_logistics_delivered(order: Order) -> bool:
    logistics = getattr(order, 'logistics', None)
    if logistics is None:
        try:
            logistics = order.logistics
        except Logistics.DoesNotExist:
            return False
    if logistics.status == Logistics.STATUS_DELIVERED:
        return True
    for trace in logistics.traces or []:
        content = str(trace.get('content') or trace.get('status') or '')
        if any(keyword in content for keyword in ('签收', '已送达', '已领取', '本人签收')):
            return True
    return False


def _notify_receipt_completed(order: Order, *, old_status: str) -> None:
    try:
        from notification.services import notify_order_status, notify_tenant_order_completed

        notify_order_status(order=order, old_status=old_status)
        notify_tenant_order_completed(order=order)
    except Exception:
        logger.exception('Notify receipt completed failed for order %s', order.order_no)


@transaction.atomic
def confirm_order_receipt(
    order: Order,
    customer,
    *,
    early_acknowledged: bool = False,
) -> tuple[Order, str]:
    locked = Order.objects.select_for_update().select_related('logistics').get(pk=order.pk)
    if locked.customer_id != customer.id:
        raise ValueError('无权操作该订单')
    if locked.status != Order.STATUS_SHIPPED:
        raise ValueError('当前订单不可确认收货')

    delivered = is_logistics_delivered(locked)
    if not delivered and not early_acknowledged:
        raise LogisticsNotDeliveredError('物流尚未显示签收')

    receipt_type = RECEIPT_TYPE_NORMAL if delivered else RECEIPT_TYPE_EARLY
    old_status = locked.status
    now = timezone.now()
    locked.status = Order.STATUS_COMPLETED
    locked.completed_at = now
    locked.receipt_type = receipt_type
    locked.save(update_fields=['status', 'completed_at', 'receipt_type', 'updated_at'])
    _notify_receipt_completed(locked, old_status=old_status)
    return locked, receipt_type


@transaction.atomic
def auto_confirm_order_receipt(order: Order) -> bool:
    locked = Order.objects.select_for_update().filter(
        pk=order.pk,
        status=Order.STATUS_SHIPPED,
    ).first()
    if locked is None:
        return False
    old_status = locked.status
    now = timezone.now()
    locked.status = Order.STATUS_COMPLETED
    locked.completed_at = now
    locked.receipt_type = RECEIPT_TYPE_AUTO
    locked.save(update_fields=['status', 'completed_at', 'receipt_type', 'updated_at'])
    _notify_receipt_completed(locked, old_status=old_status)
    return True


def run_auto_confirm_receipts() -> int:
    """Confirm shipped orders older than RECEIPT_AUTO_CONFIRM_DAYS."""
    from django.db.models import Q

    cutoff = timezone.now() - timedelta(days=RECEIPT_AUTO_CONFIRM_DAYS)
    candidates = Order.objects.filter(status=Order.STATUS_SHIPPED).filter(
        Q(shipped_at__lte=cutoff) | Q(shipped_at__isnull=True, updated_at__lte=cutoff),
    )
    count = 0
    for order in candidates.iterator():
        try:
            if auto_confirm_order_receipt(order):
                count += 1
        except Exception:
            logger.exception('Auto confirm receipt failed for order %s', order.order_no)
    return count
