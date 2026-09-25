"""Complaint notification helpers."""

from django.utils import timezone

from notification.models import Notification
from notification.services import create_notification, notify_staff_by_roles


def notify_complaint_created(*, complaint) -> None:
    if not complaint.tenant_id:
        return
    tenant_name = complaint.tenant.name
    title = f'新投诉 {complaint.complaint_no}'
    content = f'{tenant_name}：{complaint.title or complaint.get_category_display()}'
    create_notification(
        recipient_type=Notification.RECIPIENT_TENANT,
        recipient_id=complaint.tenant_id,
        title=title,
        content=content,
        notification_type=Notification.TYPE_COMPLAINT,
        related_url='/complaints',
        related_id=complaint.id,
        level='urgent',
    )


def notify_merchant_replied(*, complaint) -> None:
    if not complaint.customer_id:
        return
    create_notification(
        recipient_type=Notification.RECIPIENT_CUSTOMER,
        recipient_id=complaint.customer_id,
        title=f'商户已回复投诉 {complaint.complaint_no}',
        content='商户已回复您的投诉，请查看并确认是否解决',
        notification_type=Notification.TYPE_COMPLAINT,
        related_url=f'/complaints/{complaint.id}',
        related_id=complaint.id,
    )


def notify_customer_reviewed(*, complaint, satisfied: bool) -> None:
    if satisfied:
        if complaint.tenant_id:
            create_notification(
                recipient_type=Notification.RECIPIENT_TENANT,
                recipient_id=complaint.tenant_id,
                title=f'投诉已解决 {complaint.complaint_no}',
                content='用户已确认投诉问题已解决',
                notification_type=Notification.TYPE_COMPLAINT,
                related_url='/complaints',
                related_id=complaint.id,
            )
        return
    if complaint.tenant_id:
        create_notification(
            recipient_type=Notification.RECIPIENT_TENANT,
            recipient_id=complaint.tenant_id,
            title=f'用户不满意处理结果 {complaint.complaint_no}',
            content='用户对处理结果不满意，请继续跟进',
            notification_type=Notification.TYPE_COMPLAINT,
            related_url='/complaints',
            related_id=complaint.id,
            level='urgent',
        )


def notify_platform_intervention_requested(*, complaint) -> None:
    from tenants.notify import push_admin_alert

    title = f'用户申请平台介入 {complaint.complaint_no}'
    order_no = complaint.order.order_no if complaint.order_id else '-'
    content = f'订单 {order_no} 投诉需平台仲裁'
    push_admin_alert({
        'type': 'system_alert',
        'level': 'urgent',
        'title': title,
        'content': content,
        'target_url': f'/customers/complaints/{complaint.id}',
        'complaint_id': complaint.id,
        'timestamp': timezone.now().isoformat(),
    })
    notify_staff_by_roles(
        ['cs_staff', 'cs_manager', 'super_admin'],
        title=title,
        content=content,
        notification_type=Notification.TYPE_COMPLAINT,
        related_url=f'/customers/complaints/{complaint.id}',
        related_id=complaint.id,
        level='urgent',
        push_ws=False,
    )


def notify_platform_decided(*, complaint) -> None:
    decision_label = complaint.get_platform_decision_display() if complaint.platform_decision else '已处理'
    if complaint.customer_id:
        create_notification(
            recipient_type=Notification.RECIPIENT_CUSTOMER,
            recipient_id=complaint.customer_id,
            title=f'平台仲裁完成 {complaint.complaint_no}',
            content=f'平台裁决：{decision_label}。{(complaint.resolution or "")[:120]}',
            notification_type=Notification.TYPE_COMPLAINT,
            related_url=f'/complaints/{complaint.id}',
            related_id=complaint.id,
        )
    if complaint.tenant_id:
        create_notification(
            recipient_type=Notification.RECIPIENT_TENANT,
            recipient_id=complaint.tenant_id,
            title=f'平台仲裁完成 {complaint.complaint_no}',
            content=f'平台裁决：{decision_label}',
            notification_type=Notification.TYPE_COMPLAINT,
            related_url='/complaints',
            related_id=complaint.id,
        )
