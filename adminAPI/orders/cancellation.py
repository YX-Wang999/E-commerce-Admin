"""Order cancellation business logic."""

from __future__ import annotations

import logging

from django.db import transaction
from django.utils import timezone

from orders.models import CancelLog, Order
from products.inventory import set_inventory_context
from products.models import InventoryLog, Product

logger = logging.getLogger(__name__)


def _write_cancel_log(
    order: Order,
    *,
    action: str,
    reason: str = '',
    remark: str = '',
    operator_type: str = CancelLog.OPERATOR_SYSTEM,
    operator_id: str = '',
) -> None:
    CancelLog.objects.create(
        order=order,
        action=action,
        reason=reason[:255],
        remark=remark[:255],
        operator_type=operator_type,
        operator_id=str(operator_id or ''),
    )


def _restore_order_resources(order: Order, *, inventory_remark: str) -> None:
    for item in order.items.select_related('product'):
        product = Product.objects.select_for_update().get(pk=item.product_id)
        set_inventory_context(
            order=order,
            change_type=InventoryLog.TYPE_RETURN_IN,
            remark=inventory_remark,
        )
        product.stock += item.quantity
        product.save(update_fields=['stock', 'updated_at'])

    try:
        from promotion.services import release_user_coupon_for_order
        from points.checkout import refund_points_for_order

        release_user_coupon_for_order(order)
        if order.customer_id and order.points_used > 0:
            refund_points_for_order(order.customer, order)
        if order.customer_id and order.tenant_id and order.seller_points_used > 0:
            from seller_points.services import refund_seller_points_for_order

            refund_seller_points_for_order(order)
    except Exception:
        logger.exception('Restore promotion resources failed for order %s', order.order_no)


@transaction.atomic
def process_order_cancellation(
    order: Order,
    *,
    cancel_type: str,
    cancel_reason: str,
    action: str,
    operator_type: str,
    operator_id: str = '',
    remark: str = '',
    needs_refund: bool = False,
) -> Order:
    """Unified cancellation handler: restore resources and mark order cancelled."""
    locked = Order.objects.select_for_update().get(pk=order.pk)
    if locked.status == Order.STATUS_CANCELLED:
        return locked

    was_paid = locked.status in {Order.STATUS_PAID, Order.STATUS_REFUNDING} or bool(locked.paid_at)
    _restore_order_resources(locked, inventory_remark=f'订单取消 {locked.order_no}')

    locked.status = Order.STATUS_CANCELLED
    locked.cancel_type = cancel_type
    locked.cancel_reason = cancel_reason
    locked.cancel_status = Order.CANCEL_STATUS_NONE
    locked.cancelled_at = timezone.now()
    locked.save(
        update_fields=[
            'status',
            'cancel_type',
            'cancel_reason',
            'cancel_status',
            'cancelled_at',
            'updated_at',
        ],
    )

    _write_cancel_log(
        locked,
        action=action,
        reason=cancel_reason,
        remark=remark,
        operator_type=operator_type,
        operator_id=operator_id,
    )

    if needs_refund and was_paid:
        logger.info('Mock refund triggered for cancelled order %s amount=%s', locked.order_no, locked.total_amount)

    try:
        from notification.services import notify_order_cancelled

        notify_order_cancelled(order=locked, action=action, remark=remark)
    except Exception:
        logger.exception('Notify order cancelled failed for order %s', locked.order_no)

    return locked


@transaction.atomic
def cancel_pending_order_by_customer(order: Order, customer, *, reason: str, detail: str = '') -> Order:
    locked = Order.objects.select_for_update().get(pk=order.pk)
    if locked.customer_id != customer.id:
        raise ValueError('无权操作该订单')
    if locked.status != Order.STATUS_PENDING:
        raise ValueError('当前订单状态不可直接取消')
    if locked.expires_at and locked.expires_at <= timezone.now():
        raise ValueError('订单已过期')

    return process_order_cancellation(
        locked,
        cancel_type=Order.CANCEL_TYPE_USER,
        cancel_reason=reason or '用户取消',
        action=CancelLog.ACTION_USER_DIRECT,
        operator_type=CancelLog.OPERATOR_CUSTOMER,
        operator_id=str(customer.id),
        remark=detail,
    )


@transaction.atomic
def apply_cancel_order_by_customer(order: Order, customer, *, reason: str, detail: str = '') -> Order:
    locked = Order.objects.select_for_update().get(pk=order.pk)
    if locked.customer_id != customer.id:
        raise ValueError('无权操作该订单')
    if locked.status != Order.STATUS_PAID:
        raise ValueError('仅待发货订单可申请取消')
    if locked.cancel_status == Order.CANCEL_STATUS_PENDING:
        raise ValueError('取消申请审核中，请勿重复提交')

    locked.cancel_status = Order.CANCEL_STATUS_PENDING
    locked.cancel_reason = reason
    locked.cancel_detail = detail
    locked.cancel_review_remark = ''
    locked.save(
        update_fields=[
            'cancel_status',
            'cancel_reason',
            'cancel_detail',
            'cancel_review_remark',
            'updated_at',
        ],
    )
    _write_cancel_log(
        locked,
        action=CancelLog.ACTION_USER_APPLY,
        reason=reason,
        remark=detail,
        operator_type=CancelLog.OPERATOR_CUSTOMER,
        operator_id=str(customer.id),
    )

    try:
        from notification.services import notify_cancel_apply

        notify_cancel_apply(order=locked)
    except Exception:
        logger.exception('Notify cancel apply failed for order %s', locked.order_no)

    return locked


@transaction.atomic
def review_cancel_apply(
    order: Order,
    *,
    approve: bool,
    remark: str = '',
    operator_id: str = '',
    operator_type: str = CancelLog.OPERATOR_MERCHANT,
) -> Order:
    locked = Order.objects.select_for_update().get(pk=order.pk)
    if locked.status != Order.STATUS_PAID:
        raise ValueError('订单状态已变更，无法审核')
    if locked.cancel_status != Order.CANCEL_STATUS_PENDING:
        raise ValueError('该订单没有待审核的取消申请')

    if approve:
        return process_order_cancellation(
            locked,
            cancel_type=Order.CANCEL_TYPE_MERCHANT,
            cancel_reason=locked.cancel_reason or '同意取消',
            action=CancelLog.ACTION_MERCHANT_APPROVE,
            operator_type=operator_type,
            operator_id=operator_id,
            remark=remark,
            needs_refund=True,
        )

    locked.cancel_status = Order.CANCEL_STATUS_REJECTED
    locked.cancel_review_remark = remark
    locked.save(update_fields=['cancel_status', 'cancel_review_remark', 'updated_at'])
    _write_cancel_log(
        locked,
        action=CancelLog.ACTION_MERCHANT_REJECT,
        reason=locked.cancel_reason,
        remark=remark,
        operator_type=operator_type,
        operator_id=operator_id,
    )

    try:
        from notification.services import notify_cancel_rejected

        notify_cancel_rejected(order=locked, remark=remark)
    except Exception:
        logger.exception('Notify cancel rejected failed for order %s', locked.order_no)

    return locked


@transaction.atomic
def review_cancel_apply_by_merchant(
    order: Order,
    *,
    approve: bool,
    remark: str = '',
    operator_id: str = '',
) -> Order:
    return review_cancel_apply(
        order,
        approve=approve,
        remark=remark,
        operator_id=operator_id,
        operator_type=CancelLog.OPERATOR_MERCHANT,
    )


@transaction.atomic
def review_cancel_apply_by_platform(
    order: Order,
    *,
    approve: bool,
    remark: str = '',
    operator_id: str = '',
) -> Order:
    return review_cancel_apply(
        order,
        approve=approve,
        remark=remark,
        operator_id=operator_id,
        operator_type=CancelLog.OPERATOR_STAFF,
    )


@transaction.atomic
def cancel_order_by_merchant(order: Order, *, reason: str, operator_id: str = '') -> Order:
    locked = Order.objects.select_for_update().get(pk=order.pk)
    if locked.status != Order.STATUS_PAID:
        raise ValueError('仅待发货订单可由商户取消')
    return process_order_cancellation(
        locked,
        cancel_type=Order.CANCEL_TYPE_MERCHANT,
        cancel_reason=reason or '商户取消订单',
        action=CancelLog.ACTION_MERCHANT_CANCEL,
        operator_type=CancelLog.OPERATOR_MERCHANT,
        operator_id=operator_id,
        needs_refund=True,
    )


@transaction.atomic
def cancel_order_by_platform(order: Order, *, reason: str, operator_id: str = '') -> Order:
    locked = Order.objects.select_for_update().get(pk=order.pk)
    if locked.status == Order.STATUS_CANCELLED:
        return locked
    if locked.status in {Order.STATUS_SHIPPED, Order.STATUS_COMPLETED}:
        raise ValueError('已发货/已完成订单不可强制取消，请走售后流程')

    needs_refund = locked.status in {Order.STATUS_PAID, Order.STATUS_REFUNDING} or bool(locked.paid_at)
    return process_order_cancellation(
        locked,
        cancel_type=Order.CANCEL_TYPE_PLATFORM,
        cancel_reason=reason or '平台强制取消',
        action=CancelLog.ACTION_PLATFORM_CANCEL,
        operator_type=CancelLog.OPERATOR_STAFF,
        operator_id=operator_id,
        needs_refund=needs_refund,
    )


@transaction.atomic
def cancel_timeout_order(order: Order) -> bool:
    locked = Order.objects.select_for_update().filter(
        pk=order.pk,
        status=Order.STATUS_PENDING,
        expires_at__lte=timezone.now(),
    ).first()
    if locked is None:
        return False

    process_order_cancellation(
        locked,
        cancel_type=Order.CANCEL_TYPE_TIMEOUT,
        cancel_reason='支付超时自动取消',
        action=CancelLog.ACTION_AUTO,
        operator_type=CancelLog.OPERATOR_SYSTEM,
    )
    return True


def release_failed_group_orders() -> int:
    """Cancel pending orders whose group buy failed due to timeout."""
    from promotion.models import GroupOrder

    now = timezone.now()
    failed_groups = GroupOrder.objects.filter(
        status=GroupOrder.STATUS_PENDING,
        expired_at__lte=now,
    ).select_related('order')
    count = 0
    for group_order in failed_groups:
        try:
            with transaction.atomic():
                locked_group = GroupOrder.objects.select_for_update().get(pk=group_order.pk)
                if locked_group.status != GroupOrder.STATUS_PENDING:
                    continue
                locked_group.status = GroupOrder.STATUS_FAILED
                locked_group.save(update_fields=['status'])
                order = Order.objects.select_for_update().get(pk=locked_group.order_id)
                if order.status == Order.STATUS_PENDING:
                    process_order_cancellation(
                        order,
                        cancel_type=Order.CANCEL_TYPE_GROUPBUY,
                        cancel_reason='团购超时未成团，订单自动取消',
                        action=CancelLog.ACTION_AUTO,
                        operator_type=CancelLog.OPERATOR_SYSTEM,
                    )
                    count += 1
        except Exception:
            logger.exception('Cancel failed group order failed: group_order=%s', group_order.id)
    return count
