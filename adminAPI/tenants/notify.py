"""WebSocket + inbox notification helpers for tenants."""

from __future__ import annotations

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.utils import timezone

from tenants.models import TenantAppeal, TenantAppealMessage, TenantInboxMessage

User = get_user_model()


def push_customer_notify(customer_id: int, payload: dict) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        f'customer_notify_{customer_id}',
        {'type': 'notify.event', 'payload': payload},
    )


def push_seller_notify(tenant_id: int, payload: dict) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        f'seller_notify_{tenant_id}',
        {'type': 'notify.event', 'payload': payload},
    )


def push_admin_alert(payload: dict) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        'admin_notify',
        {'type': 'notify.event', 'payload': payload},
    )


def push_staff_notify(user_id: int, payload: dict) -> None:
    """Push to a single staff user's WebSocket group."""
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        f'staff_notify_{user_id}',
        {'type': 'notify.event', 'payload': payload},
    )


def push_cart_update(customer_id: int, *, count: int) -> None:
    """Notify mall client that cart item count changed."""
    push_customer_notify(
        customer_id,
        {
            'type': 'cart_update',
            'count': count,
            'timestamp': timezone.now().isoformat(),
        },
    )


def record_platform_appeal_reply(
    *,
    appeal: TenantAppeal,
    reply_content: str,
    operator: User,
    status: str,
) -> TenantInboxMessage:
    appeal.reply = reply_content
    appeal.status = status
    appeal.operator = operator
    appeal.save(update_fields=['reply', 'status', 'operator', 'updated_at'])

    TenantAppealMessage.objects.create(
        appeal=appeal,
        sender_type=TenantAppealMessage.SENDER_PLATFORM,
        sender_user=operator,
        content=reply_content,
    )

    inbox = TenantInboxMessage.objects.create(
        tenant=appeal.tenant,
        appeal=appeal,
        message_type=TenantInboxMessage.TYPE_APPEAL_REPLY,
        title='您的申诉有了新回复',
        content=reply_content,
        is_read=False,
    )

    push_seller_notify(
        appeal.tenant_id,
        {
            'type': 'appeal_reply',
            'level': 'urgent',
            'title': inbox.title,
            'content': reply_content,
            'appeal_id': appeal.id,
            'inbox_id': inbox.id,
            'status': appeal.status,
            'timestamp': inbox.created_at.isoformat(),
        },
    )
    return inbox


def record_merchant_appeal_reply(*, appeal: TenantAppeal, user: User, content: str) -> TenantAppealMessage:
    message = TenantAppealMessage.objects.create(
        appeal=appeal,
        sender_type=TenantAppealMessage.SENDER_MERCHANT,
        sender_user=user,
        content=content,
    )
    push_admin_alert(
        {
            'type': 'system_alert',
            'level': 'urgent',
            'title': f'【申诉】{appeal.tenant.name} 回复了申诉 #{appeal.id}',
            'content': content[:200],
            'target_url': '/tenants/appeals',
            'appeal_id': appeal.id,
            'tenant_id': appeal.tenant_id,
            'timestamp': message.created_at.isoformat(),
        },
    )
    return message
