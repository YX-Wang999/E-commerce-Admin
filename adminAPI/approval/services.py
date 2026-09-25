"""Unified approval services."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from approval.handlers import APPROVE_HANDLERS, REJECT_HANDLERS
from approval.models import Approval, ApprovalLog

logger = logging.getLogger(__name__)
User = get_user_model()

REVIEWER_ROLE_MAP: dict[str, list[str]] = {
    Approval.TYPE_CLOSURE: ['super_admin', 'ops_director', 'ops_manager'],
    Approval.TYPE_TAG: ['super_admin', 'ops_director', 'ops_manager'],
    Approval.TYPE_SUBSIDY: ['super_admin', 'ops_director', 'ops_manager'],
    Approval.TYPE_SECKILL: ['super_admin', 'ops_director', 'ops_manager'],
    Approval.TYPE_GROUPBUY: ['super_admin', 'ops_director', 'ops_manager'],
    Approval.TYPE_REFUND: ['cs_manager', 'cs_staff', 'super_admin'],
    Approval.TYPE_TENANT: ['super_admin', 'ops_director'],
}


def _operator_name(user: User | None) -> str:
    if user is None:
        return ''
    return user.get_full_name() or user.username or str(user.id)


def _write_log(approval: Approval, *, action: str, operator: User | None = None, remark: str = '') -> None:
    ApprovalLog.objects.create(
        approval=approval,
        action=action,
        operator_id=operator.id if operator else None,
        operator_name=_operator_name(operator),
        remark=remark,
    )


def _notify_reviewers(approval: Approval) -> None:
    from notification.models import Notification
    from notification.services import notify_staff_by_roles

    roles = REVIEWER_ROLE_MAP.get(approval.approval_type, ['super_admin', 'ops_director'])
    notify_staff_by_roles(
        roles,
        title=f'待审核：{approval.title}',
        content=approval.summary or '有新的审核申请待处理',
        notification_type=Notification.TYPE_APPROVAL_PENDING,
        related_url=approval.action_url or '/approvals',
        related_id=approval.id,
        need_popup=True,
        need_sound=True,
    )


def _notify_applicant_result(approval: Approval, *, approved: bool) -> None:
    from notification.models import Notification
    from notification.services import create_notification

    if approval.applicant_type != Approval.APPLICANT_TENANT:
        return
    if approved:
        title = f'审核通过：{approval.title}'
        content = approval.review_remark or '您的申请已审核通过'
    else:
        title = f'审核驳回：{approval.title}'
        content = approval.reject_reason or '您的申请未通过审核'
    create_notification(
        recipient_type=Notification.RECIPIENT_TENANT,
        recipient_id=approval.applicant_id,
        title=title,
        content=content,
        notification_type=Notification.TYPE_APPROVAL_RESULT,
        related_url=approval.action_url,
        related_id=approval.id,
        level='info',
    )


@transaction.atomic
def submit_approval(
    *,
    approval_type: str,
    business_type: str,
    business_id: int,
    applicant_type: str,
    applicant_id: int,
    title: str,
    summary: str = '',
    application_data: dict[str, Any] | None = None,
    action_url: str = '',
    priority: str = Approval.PRIORITY_NORMAL,
    timeout_hours: int | None = 72,
    notify: bool = True,
) -> Approval:
    """Create or refresh a pending approval for a business record."""
    timeout_at = timezone.now() + timedelta(hours=timeout_hours) if timeout_hours else None
    approval, created = Approval.objects.update_or_create(
        business_type=business_type,
        business_id=business_id,
        defaults={
            'approval_type': approval_type,
            'title': title,
            'summary': summary,
            'application_data': application_data or {},
            'action_url': action_url,
            'applicant_type': applicant_type,
            'applicant_id': applicant_id,
            'status': Approval.STATUS_PENDING,
            'priority': priority,
            'timeout_at': timeout_at,
            'reviewer': None,
            'reviewed_at': None,
            'reject_reason': '',
            'review_remark': '',
        },
    )
    if created:
        _write_log(approval, action=ApprovalLog.ACTION_SUBMIT)
        if notify:
            _notify_reviewers(approval)
    return approval


def mark_approval_finished(
    approval: Approval,
    *,
    status: str,
    reviewer: User | None = None,
    reject_reason: str = '',
    review_remark: str = '',
    notify_applicant: bool = True,
) -> Approval:
    approval.status = status
    approval.reviewer = reviewer
    approval.reviewed_at = timezone.now()
    approval.reject_reason = reject_reason
    approval.review_remark = review_remark
    approval.save(
        update_fields=[
            'status',
            'reviewer',
            'reviewed_at',
            'reject_reason',
            'review_remark',
            'updated_at',
        ],
    )
    action = ApprovalLog.ACTION_APPROVE if status == Approval.STATUS_APPROVED else ApprovalLog.ACTION_REJECT
    if status == Approval.STATUS_CANCELLED:
        action = ApprovalLog.ACTION_CANCEL
    _write_log(
        approval,
        action=action,
        operator=reviewer,
        remark=reject_reason or review_remark,
    )
    if notify_applicant and status in {Approval.STATUS_APPROVED, Approval.STATUS_REJECTED}:
        _notify_applicant_result(approval, approved=status == Approval.STATUS_APPROVED)
    return approval


@transaction.atomic
def approve_record(approval: Approval, reviewer: User, **payload: Any) -> Approval:
    if approval.status != Approval.STATUS_PENDING:
        raise ValueError('当前状态不可审核通过')
    handler = APPROVE_HANDLERS.get(approval.approval_type)
    if handler is None:
        raise ValueError('该审核类型暂未接入业务处理')
    handler(approval, reviewer, payload)
    return mark_approval_finished(
        approval,
        status=Approval.STATUS_APPROVED,
        reviewer=reviewer,
        review_remark=(payload.get('review_remark') or '').strip(),
    )


@transaction.atomic
def reject_record(approval: Approval, reviewer: User, *, reject_reason: str, **payload: Any) -> Approval:
    if approval.status != Approval.STATUS_PENDING:
        raise ValueError('当前状态不可驳回')
    reason = (reject_reason or '').strip()
    if not reason:
        raise ValueError('请填写驳回原因')
    handler = REJECT_HANDLERS.get(approval.approval_type)
    if handler is None:
        raise ValueError('该审核类型暂未接入业务处理')
    payload = {**payload, 'reject_reason': reason}
    handler(approval, reviewer, payload)
    return mark_approval_finished(
        approval,
        status=Approval.STATUS_REJECTED,
        reviewer=reviewer,
        reject_reason=reason,
    )


def get_pending_summary() -> list[dict[str, Any]]:
    rows = (
        Approval.objects.filter(status=Approval.STATUS_PENDING)
        .values('approval_type')
        .annotate(count=Count('id'))
        .order_by('approval_type')
    )
    label_map = dict(Approval.TYPE_CHOICES)
    return [
        {
            'approval_type': row['approval_type'],
            'label': label_map.get(row['approval_type'], row['approval_type']),
            'count': row['count'],
        }
        for row in rows
    ]


def sync_closure_approval(application) -> Approval | None:
    from shop_closure.models import ClosureApplication

    if application.status != ClosureApplication.STATUS_PENDING:
        Approval.objects.filter(
            business_type='shop_closure.application',
            business_id=application.id,
            status=Approval.STATUS_PENDING,
        ).update(status=Approval.STATUS_CANCELLED, updated_at=timezone.now())
        return None
    tenant = application.tenant
    return submit_approval(
        approval_type=Approval.TYPE_CLOSURE,
        business_type='shop_closure.application',
        business_id=application.id,
        applicant_type=Approval.APPLICANT_TENANT,
        applicant_id=tenant.id,
        title=f'店铺注销 - {tenant.name}',
        summary=application.reason,
        application_data={
            'tenant_name': tenant.name,
            'reason': application.reason,
            'detail': application.detail,
        },
        action_url=f'/system/closures/{application.id}',
        priority=Approval.PRIORITY_HIGH,
    )


def sync_tag_approval(config) -> Approval | None:
    from tag_system.models import TenantTagConfig

    if config.status != TenantTagConfig.STATUS_PENDING:
        Approval.objects.filter(
            business_type='tag_system.tenant_config',
            business_id=config.id,
            status=Approval.STATUS_PENDING,
        ).update(status=Approval.STATUS_CANCELLED, updated_at=timezone.now())
        return None
    tenant = config.tenant
    tag = config.tag
    return submit_approval(
        approval_type=Approval.TYPE_TAG,
        business_type='tag_system.tenant_config',
        business_id=config.id,
        applicant_type=Approval.APPLICANT_TENANT,
        applicant_id=tenant.id,
        title=f'标签参与 - {tag.name}',
        summary=f'{tenant.name} 申请参与「{tag.name}」',
        application_data={
            'tenant_name': tenant.name,
            'tag_name': tag.name,
            'tag_code': tag.code,
            'custom_name': config.custom_name,
        },
        action_url='/system/tags/review',
        priority=Approval.PRIORITY_NORMAL,
    )


def sync_subsidy_approval(row) -> Approval | None:
    from subsidy.models import SubsidyProduct

    if row.filing_status != SubsidyProduct.FILING_SUBMITTED:
        Approval.objects.filter(
            business_type='subsidy.product',
            business_id=row.id,
            status=Approval.STATUS_PENDING,
        ).update(status=Approval.STATUS_CANCELLED, updated_at=timezone.now())
        return None
    return submit_approval(
        approval_type=Approval.TYPE_SUBSIDY,
        business_type='subsidy.product',
        business_id=row.id,
        applicant_type=Approval.APPLICANT_TENANT,
        applicant_id=row.tenant_id,
        title=f'国补备案 - {row.product.name}',
        summary=f'{row.tenant.name} 提交国补备案',
        application_data={
            'product_name': row.product.name,
            'tenant_name': row.tenant.name,
            'region': row.region,
            'category': row.category,
        },
        action_url='/subsidy/products',
        priority=Approval.PRIORITY_HIGH,
    )


def sync_promotion_approval(activity, approval_type: str) -> Approval | None:
    from promotion.models import GroupBuyActivity, SeckillActivity

    pending_statuses = {SeckillActivity.STATUS_PENDING, SeckillActivity.STATUS_REVIEWING}
    if activity.status not in pending_statuses:
        Approval.objects.filter(
            business_type=f'promotion.{approval_type}',
            business_id=activity.id,
            status=Approval.STATUS_PENDING,
        ).update(status=Approval.STATUS_CANCELLED, updated_at=timezone.now())
        return None
    tenant_name = activity.tenant.name if activity.tenant_id else '平台'
    return submit_approval(
        approval_type=approval_type,
        business_type=f'promotion.{approval_type}',
        business_id=activity.id,
        applicant_type=Approval.APPLICANT_TENANT if activity.tenant_id else Approval.APPLICANT_STAFF,
        applicant_id=activity.tenant_id or (activity.created_by_id or 0),
        title=f'{"秒杀" if approval_type == Approval.TYPE_SECKILL else "团购"}活动 - {activity.name}',
        summary=f'{tenant_name} 提交活动审核',
        application_data={'activity_name': activity.name, 'tenant_name': tenant_name},
        action_url=f'/promotions/{"seckill" if approval_type == Approval.TYPE_SECKILL else "groupbuy"}',
        priority=Approval.PRIORITY_NORMAL,
    )
