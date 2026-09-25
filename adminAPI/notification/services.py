"""Notification creation and delivery helpers."""

from __future__ import annotations

import logging
from typing import Iterable

from django.contrib.auth import get_user_model
from django.utils import timezone

from notification.models import Notification

logger = logging.getLogger(__name__)
User = get_user_model()
LOW_STOCK_THRESHOLD = 10

STAFF_ORDER_ROLES = (
    'super_admin',
    'ops_manager',
    'ops_director',
    'ops_staff',
    'warehouse_manager',
)


def _notify_platform_order_event(
    *,
    title: str,
    content: str,
    related_url: str,
    order_id: int | None = None,
    notification_type: str,
    need_popup: bool = True,
    need_sound: bool = True,
) -> None:
    """Push cancel/order alerts to admin WebSocket group and staff inboxes."""
    from tenants.notify import push_admin_alert

    push_admin_alert({
        'type': 'system_alert',
        'level': 'urgent' if need_sound else 'warning',
        'title': title,
        'content': content,
        'target_url': related_url,
        'order_id': order_id,
        'timestamp': timezone.now().isoformat(),
    })
    notify_staff_by_roles(
        STAFF_ORDER_ROLES,
        title=title,
        content=content,
        notification_type=notification_type,
        related_url=related_url,
        related_id=order_id,
        level='urgent' if need_sound else 'info',
        need_popup=need_popup,
        need_sound=need_sound,
    )


def notify(
    *,
    recipient_type: str,
    recipient_id: int,
    notification_type: str,
    title: str,
    content: str,
    related_url: str = '',
    related_id: int | None = None,
    need_popup: bool = False,
    need_sound: bool = False,
    push_ws: bool = True,
    level: str = 'info',
) -> Notification:
    """Unified notification entry point for all business modules."""
    return create_notification(
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        title=title,
        content=content,
        notification_type=notification_type,
        related_url=related_url,
        related_id=related_id,
        need_popup=need_popup,
        need_sound=need_sound,
        push_ws=push_ws,
        level='urgent' if need_sound or need_popup else level,
    )


def create_notification(
    *,
    recipient_type: str,
    recipient_id: int,
    title: str,
    content: str,
    notification_type: str,
    related_url: str = '',
    related_id: int | None = None,
    need_popup: bool = False,
    need_sound: bool = False,
    push_ws: bool = True,
    level: str = 'info',
) -> Notification:
    notification = Notification.objects.create(
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        title=title,
        content=content,
        type=notification_type,
        related_url=related_url,
        related_id=related_id,
        need_popup=need_popup,
        need_sound=need_sound,
        is_sent=push_ws,
        sent_at=timezone.now() if push_ws else None,
    )
    if push_ws:
        _push_ws(notification, level=level, need_sound=need_sound)
    return notification


def _push_ws(notification: Notification, *, level: str = 'info', need_sound: bool = False) -> None:
    payload = {
        'type': 'notification',
        'level': level,
        'notification_id': notification.id,
        'title': notification.title,
        'content': notification.content[:200],
        'notification_type': notification.type,
        'related_url': notification.related_url,
        'related_id': notification.related_id,
        'need_popup': notification.need_popup,
        'need_sound': need_sound or notification.need_sound,
        'timestamp': notification.created_at.isoformat(),
    }
    try:
        if notification.recipient_type == Notification.RECIPIENT_STAFF:
            from tenants.notify import push_staff_notify

            push_staff_notify(notification.recipient_id, payload)
        elif notification.recipient_type == Notification.RECIPIENT_TENANT:
            from tenants.notify import push_seller_notify

            push_seller_notify(notification.recipient_id, payload)
        elif notification.recipient_type == Notification.RECIPIENT_CUSTOMER:
            from tenants.notify import push_customer_notify

            push_customer_notify(notification.recipient_id, payload)
    except Exception:
        logger.exception('Push notification WS failed: %s', notification.id)


def notify_staff_by_roles(
    role_codes: Iterable[str],
    *,
    title: str,
    content: str,
    notification_type: str,
    related_url: str = '',
    related_id: int | None = None,
    level: str = 'info',
    push_ws: bool = True,
    need_popup: bool = False,
    need_sound: bool = False,
) -> None:
    users = User.objects.filter(
        is_active=True,
        roles__code__in=list(role_codes),
        roles__is_active=True,
    ).distinct()
    for user in users:
        notify(
            recipient_type=Notification.RECIPIENT_STAFF,
            recipient_id=user.id,
            title=title,
            content=content,
            notification_type=notification_type,
            related_url=related_url,
            related_id=related_id,
            need_popup=need_popup,
            need_sound=need_sound,
            push_ws=push_ws,
            level=level,
        )


def notify_pending_shipment(*, order) -> None:
    """Notify staff and tenant when an order is paid and awaiting shipment."""
    from customers.models import Customer
    from tenants.notify import push_admin_alert

    order_no = order.order_no
    customer_label = ''
    if order.customer_id:
        customer = getattr(order, 'customer', None)
        if customer is None:
            customer = Customer.objects.filter(pk=order.customer_id).first()
        if customer:
            customer_label = customer.nickname or customer.phone or '客户'
    title = f'待发货 #{order_no}'
    if customer_label:
        content = f'订单 {order_no}（{customer_label}）已支付，请尽快安排发货'
    else:
        content = f'订单 {order_no} 已支付，请尽快安排发货'

    if order.tenant_id:
        notify(
            recipient_type=Notification.RECIPIENT_TENANT,
            recipient_id=order.tenant_id,
            title=f'待发货 #{order_no}',
            content='您有一笔订单已支付，请尽快发货',
            notification_type=Notification.TYPE_ORDER_PAID,
            related_url='/orders',
            related_id=order.id,
            need_popup=True,
            need_sound=True,
        )
        return

    push_admin_alert({
        'type': 'system_alert',
        'level': 'urgent',
        'title': title,
        'content': content,
        'target_url': '/orders/list?status=paid',
        'order_id': order.id,
        'timestamp': timezone.now().isoformat(),
    })

    notify_staff_by_roles(
        ['warehouse_manager', 'super_admin', 'ops_manager', 'ops_director', 'ops_staff'],
        title=title,
        content=content,
        notification_type=Notification.TYPE_ORDER,
        related_url='/orders/list?status=paid',
        related_id=order.id,
        level='urgent',
        push_ws=False,
    )


def notify_new_order(*, order) -> None:
    from orders.models import Order

    if order.status == Order.STATUS_PAID:
        notify_pending_shipment(order=order)
        return

    order_no = order.order_no
    if order.tenant_id:
        notify(
            recipient_type=Notification.RECIPIENT_TENANT,
            recipient_id=order.tenant_id,
            notification_type=Notification.TYPE_ORDER_NEW,
            title=f'新订单 #{order_no}',
            content='您有一笔新订单（待付款），请关注支付进度',
            related_url='/orders',
            related_id=order.id,
            need_popup=True,
            need_sound=True,
        )


def notify_order_status(*, order, old_status: str | None = None) -> None:
    from orders.models import Order

    if not order.customer_id:
        return
    status_labels = {
        Order.STATUS_SHIPPED: ('订单已发货', f'您的订单 {order.order_no} 已发货'),
        Order.STATUS_COMPLETED: ('订单已签收', f'您的订单 {order.order_no} 已完成'),
    }
    label = status_labels.get(order.status)
    if not label or old_status == order.status:
        return
    title, content = label
    notify(
        recipient_type=Notification.RECIPIENT_CUSTOMER,
        recipient_id=order.customer_id,
        notification_type=(
            Notification.TYPE_ORDER_SHIPPED
            if order.status == Order.STATUS_SHIPPED
            else Notification.TYPE_ORDER_COMPLETED
        ),
        title=title,
        content=content,
        related_url=f'/order/{order.id}',
        related_id=order.id,
        need_popup=order.status == Order.STATUS_SHIPPED,
    )


def notify_cancel_apply(*, order) -> None:
    title = f'取消申请 #{order.order_no}'
    content = f'用户申请取消订单，原因：{order.cancel_reason}'
    related_url = '/orders/list?status=canceling'

    if order.tenant_id:
        notify(
            recipient_type=Notification.RECIPIENT_TENANT,
            recipient_id=order.tenant_id,
            title=title,
            content=content,
            notification_type=Notification.TYPE_ORDER,
            related_url='/orders',
            related_id=order.id,
            need_popup=True,
            need_sound=True,
            level='urgent',
        )


def notify_tenant_order_completed(*, order) -> None:
    """Notify merchant when buyer confirms receipt."""
    if not order.tenant_id:
        return
    notify(
        recipient_type=Notification.RECIPIENT_TENANT,
        recipient_id=order.tenant_id,
        title=f'买家已确认收货 #{order.order_no}',
        content='用户已确认收货，订单已完成',
        notification_type=Notification.TYPE_ORDER_COMPLETED,
        related_url='/orders',
        related_id=order.id,
        need_popup=True,
        need_sound=False,
    )


def notify_cancel_rejected(*, order, remark: str = '') -> None:
    if not order.customer_id:
        return
    content = f'商户驳回了您的取消申请：{remark or order.cancel_review_remark or "请继续等待发货"}'
    create_notification(
        recipient_type=Notification.RECIPIENT_CUSTOMER,
        recipient_id=order.customer_id,
        title=f'取消申请未通过 #{order.order_no}',
        content=content,
        notification_type=Notification.TYPE_ORDER,
        related_url=f'/order/{order.id}',
        related_id=order.id,
    )


def notify_order_cancelled(*, order, action: str = '', remark: str = '') -> None:
    from orders.models import CancelLog, Order

    order_no = order.order_no
    cancel_reason = order.cancel_reason or '订单已取消'

    if order.customer_id and action in {
        CancelLog.ACTION_AUTO,
        CancelLog.ACTION_MERCHANT_APPROVE,
        CancelLog.ACTION_MERCHANT_CANCEL,
        CancelLog.ACTION_PLATFORM_CANCEL,
        CancelLog.ACTION_USER_DIRECT,
    }:
        create_notification(
            recipient_type=Notification.RECIPIENT_CUSTOMER,
            recipient_id=order.customer_id,
            title=f'订单已取消 #{order_no}',
            content=cancel_reason,
            notification_type=Notification.TYPE_ORDER_CANCELLED,
            related_url=f'/order/{order.id}',
            related_id=order.id,
        )

    seller_titles = {
        CancelLog.ACTION_USER_DIRECT: (f'订单已取消 #{order_no}', f'用户取消了订单，原因：{cancel_reason}'),
        CancelLog.ACTION_AUTO: (f'订单超时取消 #{order_no}', '订单支付超时，系统已自动取消'),
        CancelLog.ACTION_MERCHANT_APPROVE: (f'取消申请已通过 #{order_no}', f'您已同意取消，原因：{cancel_reason}'),
        CancelLog.ACTION_PLATFORM_CANCEL: (
            f'订单被平台取消 #{order_no}',
            remark or cancel_reason or '平台已强制取消该订单',
        ),
    }
    if order.tenant_id and action in seller_titles:
        seller_title, seller_content = seller_titles[action]
        notify(
            recipient_type=Notification.RECIPIENT_TENANT,
            recipient_id=order.tenant_id,
            title=seller_title,
            content=seller_content,
            notification_type=Notification.TYPE_ORDER_CANCELLED,
            related_url='/orders',
            related_id=order.id,
            need_popup=action in {CancelLog.ACTION_USER_DIRECT, CancelLog.ACTION_AUTO, CancelLog.ACTION_PLATFORM_CANCEL},
            need_sound=action in {CancelLog.ACTION_USER_DIRECT, CancelLog.ACTION_AUTO, CancelLog.ACTION_PLATFORM_CANCEL},
            level='urgent',
        )

    platform_titles = {
        CancelLog.ACTION_USER_DIRECT: (f'用户取消订单 #{order_no}', f'用户取消了订单，原因：{cancel_reason}'),
        CancelLog.ACTION_AUTO: (f'订单超时取消 #{order_no}', f'订单 {order_no} 支付超时，系统已自动取消'),
    }
    # Merchant approve/cancel notifications stay on seller side only.
    if action in platform_titles:
        platform_title, platform_content = platform_titles[action]
        _notify_platform_order_event(
            title=platform_title,
            content=platform_content,
            related_url='/orders/list?status=cancelled',
            order_id=order.id,
            notification_type=Notification.TYPE_ORDER_CANCELLED,
            need_popup=action in {CancelLog.ACTION_USER_DIRECT},
            need_sound=action in {CancelLog.ACTION_USER_DIRECT},
        )


def notify_refund_request(*, refund) -> None:
    order = refund.order
    if order.tenant_id:
        notify(
            recipient_type=Notification.RECIPIENT_TENANT,
            recipient_id=order.tenant_id,
            notification_type=Notification.TYPE_REFUND_APPLIED,
            title=f'售后待处理 #{refund.id}',
            content=f'订单 {order.order_no} 提交了退款/退货申请，请及时处理',
            related_url='/orders/refunds',
            related_id=refund.id,
            need_popup=True,
            need_sound=True,
        )
    notify_staff_by_roles(
        ['cs_staff', 'cs_manager', 'super_admin'],
        title=f'售后待审核 #{refund.id}',
        content=f'订单 {order.order_no} 提交了退款/退货申请，请及时审核',
        notification_type=Notification.TYPE_REFUND,
        related_url='/orders/refunds',
        related_id=refund.id,
        level='urgent',
    )


def notify_low_stock(*, product) -> None:
    notify_staff_by_roles(
        ['ops_manager', 'ops_director', 'warehouse_manager', 'super_admin'],
        title=f'库存预警：{product.name}',
        content=f'商品「{product.name}」库存仅剩 {product.stock} 件，请及时补货',
        notification_type=Notification.TYPE_INVENTORY,
        related_url='/products/list',
        related_id=product.id,
        level='urgent',
    )


def notify_tenant_apply(*, tenant) -> None:
    notify_staff_by_roles(
        ['super_admin', 'ops_director', 'ops_manager'],
        title=f'新商户入驻申请：{tenant.name}',
        content=f'{tenant.contact_name}（{tenant.contact_phone}）提交了入驻申请，请尽快审核',
        notification_type=Notification.TYPE_TENANT_APPLY,
        related_url='/tenants/list',
        related_id=tenant.id,
        need_popup=True,
        need_sound=True,
    )


def notify_complaint(*, complaint, conversation_id: int | None = None) -> None:
    tenant_name = complaint.tenant.name if complaint.tenant_id else '平台'
    if conversation_id:
        related_url = f'/customers/chat?conversation_id={conversation_id}'
    else:
        related_url = f'/customers/complaints/{complaint.id}'
    notify_staff_by_roles(
        ['cs_staff', 'cs_manager', 'super_admin'],
        title=f'【新投诉】#{complaint.id}',
        content=f'{tenant_name}：{complaint.get_category_display()} — {complaint.content[:120]}',
        notification_type=Notification.TYPE_COMPLAINT,
        related_url=related_url,
        related_id=complaint.id,
        need_popup=True,
        need_sound=True,
    )


def notify_feedback_reply(*, feedback) -> None:
    """Notify mall customer when staff or merchant replies to feedback."""
    from customers.models import Customer

    customer_id = feedback.customer_id
    if not customer_id and feedback.phone:
        linked = Customer.objects.filter(phone=feedback.phone, is_active=True).first()
        if linked:
            customer_id = linked.id
            if feedback.customer_id != linked.id:
                feedback.customer_id = linked.id
                feedback.save(update_fields=['customer'])
    if not customer_id:
        return
    remark = (feedback.handler_remark or '').strip()
    if not remark:
        return
    type_labels = {
        'suggestion': '建议',
        'complaint': '投诉',
        'inquiry': '咨询',
        'after_sales': '售后',
    }
    label = type_labels.get(feedback.feedback_type, '留言')
    related_url = '/suggestions' if not feedback.tenant_id else '/suggestions?scope=shop'
    create_notification(
        recipient_type=Notification.RECIPIENT_CUSTOMER,
        recipient_id=customer_id,
        title=f'您的{label}已收到回复',
        content=remark[:200],
        notification_type=Notification.TYPE_SYSTEM,
        related_url=related_url,
        related_id=feedback.id,
        level='info',
    )


def notify_review_created(*, review) -> None:
    product_name = review.product.name if review.product_id else '商品'
    if review.tenant_id:
        notify(
            recipient_type=Notification.RECIPIENT_TENANT,
            recipient_id=review.tenant_id,
            title=f'收到新评价',
            content=f'商品「{product_name}」收到 {review.rating} 星评价',
            notification_type=Notification.TYPE_SYSTEM,
            related_url='/orders',
            related_id=review.id,
            need_popup=True,
        )


def notify_review_liked(*, review_id: int, actor_id: int) -> None:
    from reviews.models import ProductReview

    review = ProductReview.objects.filter(pk=review_id).select_related('customer').first()
    if review is None or review.customer_id == actor_id:
        return
    create_notification(
        recipient_type=Notification.RECIPIENT_CUSTOMER,
        recipient_id=review.customer_id,
        title='您的评价收到点赞',
        content='有人赞了您的评价',
        notification_type=Notification.TYPE_SYSTEM,
        related_url=f'/reviews/{review.id}',
        related_id=review.id,
    )


def notify_review_commented(*, review_id: int, actor_id: int, comment_id: int) -> None:
    from reviews.models import ProductReview

    review = ProductReview.objects.filter(pk=review_id).select_related('customer').first()
    if review is None or review.customer_id == actor_id:
        return
    create_notification(
        recipient_type=Notification.RECIPIENT_CUSTOMER,
        recipient_id=review.customer_id,
        title='您的评价收到评论',
        content='有人评论了您的评价',
        notification_type=Notification.TYPE_SYSTEM,
        related_url=f'/reviews/{review.id}',
        related_id=comment_id,
    )


def notify_points_mall_exchanged(*, order) -> None:
    create_notification(
        recipient_type=Notification.RECIPIENT_CUSTOMER,
        recipient_id=order.customer_id,
        title='积分兑换成功',
        content=f'您已成功兑换「{order.item_name}」，消耗 {order.points_spent} 积分',
        notification_type=Notification.TYPE_POINTS,
        related_url='/points-mall/orders',
        related_id=order.id,
    )


def notify_points_mall_shipped(*, order) -> None:
    create_notification(
        recipient_type=Notification.RECIPIENT_CUSTOMER,
        recipient_id=order.customer_id,
        title='积分兑换已发货',
        content=f'「{order.item_name}」已发货，物流单号 {order.logistics_no}',
        notification_type=Notification.TYPE_POINTS,
        related_url=f'/points-mall/orders/{order.id}',
        related_id=order.id,
    )


def notify_points_expiry_reminder(*, customer_id: int, account_id: int, balance: int, days_left: int) -> None:
    create_notification(
        recipient_type=Notification.RECIPIENT_CUSTOMER,
        recipient_id=customer_id,
        title='积分即将过期',
        content=f'您的 {balance} 积分将在 {days_left} 天后过期，请尽快使用',
        notification_type=Notification.TYPE_POINTS,
        related_url=f'/points?expire_remind={days_left}&account={account_id}',
        related_id=account_id,
    )


def notify_points_expired(*, customer_id: int, amount: int) -> None:
    create_notification(
        recipient_type=Notification.RECIPIENT_CUSTOMER,
        recipient_id=customer_id,
        title='积分已过期',
        content=f'您的 {amount} 积分已过期，积分有效期已结束',
        notification_type=Notification.TYPE_POINTS,
        related_url='/points',
        related_id=customer_id,
    )
