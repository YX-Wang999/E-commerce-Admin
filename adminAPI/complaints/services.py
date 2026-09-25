"""Complaint dispute business logic."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from chat.models import Complaint, ComplaintMessage
from orders.models import Order


def _add_message(
    *,
    complaint: Complaint,
    sender_type: str,
    sender_id: int,
    content: str,
    attachments: list | None = None,
    is_internal: bool = False,
) -> ComplaintMessage:
    return ComplaintMessage.objects.create(
        complaint=complaint,
        sender_type=sender_type,
        sender_id=sender_id,
        content=content.strip(),
        attachments=attachments or [],
        is_internal=is_internal,
    )


def validate_order_for_complaint(*, customer, order_id: int, tenant_id: int) -> Order:
    try:
        order = Order.objects.select_related('tenant').get(pk=order_id, customer=customer)
    except Order.DoesNotExist:
        raise ValueError('订单不存在或无权操作')
    if order.tenant_id != tenant_id:
        raise ValueError('订单与商户不匹配')
    if order.status not in {Order.STATUS_PAID, Order.STATUS_SHIPPED, Order.STATUS_COMPLETED, Order.STATUS_REFUNDING}:
        raise ValueError('当前订单状态不可投诉')
    open_exists = Complaint.objects.filter(
        order=order,
        customer=customer,
    ).exclude(status__in=[Complaint.STATUS_CLOSED, Complaint.STATUS_RESOLVED, Complaint.STATUS_REJECTED]).exists()
    if open_exists:
        raise ValueError('该订单已有进行中的投诉')
    return order


@transaction.atomic
def create_complaint(
    *,
    customer,
    tenant_id: int,
    order_id: int,
    category: str,
    title: str,
    content: str,
    attachments: list | None = None,
) -> Complaint:
    from tenants.models import Tenant

    tenant = Tenant.objects.filter(pk=tenant_id, status=Tenant.STATUS_ACTIVE, is_active=True).first()
    if tenant is None:
        raise ValueError('商户不存在或未入驻')
    order = validate_order_for_complaint(customer=customer, order_id=order_id, tenant_id=tenant_id)
    complaint = Complaint.objects.create(
        customer=customer,
        tenant=tenant,
        order=order,
        category=category,
        title=title.strip(),
        content=content.strip(),
        attachments=attachments or [],
        status=Complaint.STATUS_PENDING,
    )
    _add_message(
        complaint=complaint,
        sender_type=ComplaintMessage.SENDER_CUSTOMER,
        sender_id=customer.id,
        content=content.strip(),
        attachments=attachments or [],
    )
    from complaints.notify import notify_complaint_created

    notify_complaint_created(complaint=complaint)
    return complaint


@transaction.atomic
def merchant_reply_complaint(
    *,
    complaint: Complaint,
    tenant_id: int,
    content: str,
    attachments: list | None = None,
    mark_processed: bool = False,
) -> Complaint:
    if complaint.tenant_id != tenant_id:
        raise ValueError('无权处理该投诉')
    if complaint.status not in {
        Complaint.STATUS_PENDING,
        Complaint.STATUS_MERCHANT_PROCESSING,
    }:
        raise ValueError('当前状态不可回复')
    _add_message(
        complaint=complaint,
        sender_type=ComplaintMessage.SENDER_MERCHANT,
        sender_id=tenant_id,
        content=content,
        attachments=attachments,
    )
    complaint.merchant_reply = content.strip()
    complaint.merchant_replied_at = timezone.now()
    complaint.status = (
        Complaint.STATUS_CUSTOMER_REVIEW if mark_processed else Complaint.STATUS_MERCHANT_PROCESSING
    )
    complaint.save(
        update_fields=['merchant_reply', 'merchant_replied_at', 'status', 'updated_at'],
    )
    from complaints.notify import notify_merchant_replied

    notify_merchant_replied(complaint=complaint)
    return complaint


@transaction.atomic
def customer_review_complaint(*, complaint: Complaint, customer_id: int, satisfied: bool, comment: str = '') -> Complaint:
    if complaint.customer_id != customer_id:
        raise ValueError('无权操作该投诉')
    if complaint.status != Complaint.STATUS_CUSTOMER_REVIEW:
        raise ValueError('当前状态不可确认')
    if comment.strip():
        _add_message(
            complaint=complaint,
            sender_type=ComplaintMessage.SENDER_CUSTOMER,
            sender_id=customer_id,
            content=comment.strip(),
        )
    complaint.customer_satisfied = satisfied
    complaint.customer_reviewed_at = timezone.now()
    if satisfied:
        complaint.status = Complaint.STATUS_RESOLVED
        complaint.resolution = '用户确认问题已解决'
        complaint.resolved_at = timezone.now()
    else:
        complaint.status = Complaint.STATUS_MERCHANT_PROCESSING
    complaint.save(
        update_fields=[
            'customer_satisfied',
            'customer_reviewed_at',
            'status',
            'resolution',
            'resolved_at',
            'updated_at',
        ],
    )
    from complaints.notify import notify_customer_reviewed

    notify_customer_reviewed(complaint=complaint, satisfied=satisfied)
    return complaint


@transaction.atomic
def request_platform_intervention(*, complaint: Complaint, customer_id: int, reason: str = '') -> Complaint:
    if complaint.customer_id != customer_id:
        raise ValueError('无权操作该投诉')
    if complaint.status not in {
        Complaint.STATUS_CUSTOMER_REVIEW,
        Complaint.STATUS_MERCHANT_PROCESSING,
        Complaint.STATUS_PENDING,
    }:
        raise ValueError('当前状态不可申请平台介入')
    if reason.strip():
        _add_message(
            complaint=complaint,
            sender_type=ComplaintMessage.SENDER_CUSTOMER,
            sender_id=customer_id,
            content=f'申请平台介入：{reason.strip()}',
        )
    complaint.status = Complaint.STATUS_PLATFORM_REVIEWING
    complaint.save(update_fields=['status', 'updated_at'])
    from complaints.notify import notify_platform_intervention_requested

    notify_platform_intervention_requested(complaint=complaint)
    return complaint


@transaction.atomic
def platform_review_complaint(
    *,
    complaint: Complaint,
    reviewer,
    decision: str,
    platform_remark: str,
    resolution: str = '',
    internal_note: str = '',
) -> Complaint:
    if complaint.status != Complaint.STATUS_PLATFORM_REVIEWING:
        raise ValueError('当前状态不可仲裁')
    if internal_note.strip():
        _add_message(
            complaint=complaint,
            sender_type=ComplaintMessage.SENDER_PLATFORM,
            sender_id=reviewer.id,
            content=internal_note.strip(),
            is_internal=True,
        )
    public_remark = platform_remark.strip()
    if public_remark:
        _add_message(
            complaint=complaint,
            sender_type=ComplaintMessage.SENDER_PLATFORM,
            sender_id=reviewer.id,
            content=public_remark,
        )
    complaint.platform_decision = decision
    complaint.platform_remark = public_remark
    complaint.platform_reply = public_remark
    complaint.reviewed_by = reviewer
    complaint.platform_reviewed_at = timezone.now()
    complaint.resolution = resolution.strip() or public_remark
    if decision == Complaint.DECISION_DISMISS:
        complaint.status = Complaint.STATUS_REJECTED
    else:
        complaint.status = Complaint.STATUS_RESOLVED
    complaint.resolved_at = timezone.now()
    complaint.save(
        update_fields=[
            'platform_decision',
            'platform_remark',
            'platform_reply',
            'reviewed_by',
            'platform_reviewed_at',
            'resolution',
            'status',
            'resolved_at',
            'updated_at',
        ],
    )
    from complaints.notify import notify_platform_decided

    notify_platform_decided(complaint=complaint)
    return complaint


@transaction.atomic
def close_complaint(*, complaint: Complaint) -> Complaint:
    if complaint.status not in {Complaint.STATUS_RESOLVED, Complaint.STATUS_REJECTED}:
        raise ValueError('仅已解决或已驳回的投诉可关闭')
    complaint.status = Complaint.STATUS_CLOSED
    complaint.save(update_fields=['status', 'updated_at'])
    return complaint


@transaction.atomic
def add_complaint_message(
    *,
    complaint: Complaint,
    sender_type: str,
    sender_id: int,
    content: str,
    attachments: list | None = None,
    is_internal: bool = False,
) -> ComplaintMessage:
    if complaint.status in {Complaint.STATUS_CLOSED, Complaint.STATUS_REJECTED}:
        raise ValueError('投诉已结束，无法发送消息')
    if is_internal and sender_type != ComplaintMessage.SENDER_PLATFORM:
        raise ValueError('仅平台可发送内部备注')
    return _add_message(
        complaint=complaint,
        sender_type=sender_type,
        sender_id=sender_id,
        content=content,
        attachments=attachments,
        is_internal=is_internal,
    )
