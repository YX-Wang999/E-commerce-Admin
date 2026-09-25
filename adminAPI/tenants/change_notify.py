"""Notifications for tenant profile changes."""

from __future__ import annotations

from tenants.change_constants import FIELD_LABELS
from tenants.models import TenantChangeLog, TenantInboxMessage


def notify_platform_pending_change(*, tenant, fields: list[str]) -> None:
    labels = '、'.join(FIELD_LABELS.get(f, f) for f in fields)
    from notification.models import Notification
    from notification.services import notify_staff_by_roles

    notify_staff_by_roles(
        ['super_admin', 'ops_director', 'ops_manager'],
        title=f'商户信息变更待审核：{tenant.name}',
        content=f'商户提交了 {labels} 变更，请尽快审核',
        notification_type=Notification.TYPE_TENANT,
        related_url=f'/tenants/{tenant.id}?tab=changes',
        related_id=tenant.id,
        level='urgent',
    )
    from tenants.notify import push_admin_alert

    push_admin_alert(
        {
            'type': 'system_alert',
            'level': 'urgent',
            'title': f'【变更审核】{tenant.name}',
            'content': f'{labels} 待审核',
            'target_url': f'/tenants/{tenant.id}?tab=changes',
            'tenant_id': tenant.id,
        },
    )


def notify_merchant_change_reviewed(*, log: TenantChangeLog, approved: bool) -> None:
    label = FIELD_LABELS.get(log.field, log.field)
    if approved:
        title = '信息变更已通过'
        content = f'您提交的「{label}」变更已审核通过'
    else:
        title = '信息变更被驳回'
        content = f'您提交的「{label}」变更未通过'
        if log.review_remark:
            content += f'：{log.review_remark}'

    TenantInboxMessage.objects.create(
        tenant=log.tenant,
        message_type=TenantInboxMessage.TYPE_SYSTEM,
        title=title,
        content=content,
        is_read=False,
    )

    from notification.models import Notification
    from notification.services import create_notification

    create_notification(
        recipient_type=Notification.RECIPIENT_TENANT,
        recipient_id=log.tenant_id,
        title=title,
        content=content,
        notification_type=Notification.TYPE_TENANT,
        related_url='/settings',
        related_id=log.id,
        level='info',
    )
