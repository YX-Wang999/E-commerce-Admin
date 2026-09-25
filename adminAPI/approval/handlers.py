"""Approval business handlers."""

from __future__ import annotations

from typing import Any, Callable

from django.contrib.auth import get_user_model

from approval.models import Approval

User = get_user_model()
Handler = Callable[[Approval, User, dict[str, Any]], None]


def _approve_closure(approval: Approval, reviewer: User, payload: dict[str, Any]) -> None:
    from shop_closure.models import ClosureApplication
    from shop_closure.services import approve_closure_application

    application = ClosureApplication.objects.get(pk=approval.business_id)
    approve_closure_application(
        application,
        reviewer,
        notice_days=payload.get('notice_days'),
    )


def _reject_closure(approval: Approval, reviewer: User, payload: dict[str, Any]) -> None:
    from shop_closure.models import ClosureApplication
    from shop_closure.services import reject_closure_application

    application = ClosureApplication.objects.get(pk=approval.business_id)
    reject_closure_application(
        application,
        reviewer,
        reject_reason=payload.get('reject_reason', ''),
    )


def _approve_tag(approval: Approval, reviewer: User, payload: dict[str, Any]) -> None:
    from tag_system.models import TenantTagConfig

    row = TenantTagConfig.objects.select_related('tenant', 'tag').get(pk=approval.business_id)
    row.status = TenantTagConfig.STATUS_APPROVED
    row.is_participating = True
    row.reject_reason = ''
    row.save(update_fields=['status', 'is_participating', 'reject_reason', 'updated_at'])


def _reject_tag(approval: Approval, reviewer: User, payload: dict[str, Any]) -> None:
    from tag_system.models import TenantTagConfig

    row = TenantTagConfig.objects.select_related('tenant', 'tag').get(pk=approval.business_id)
    row.status = TenantTagConfig.STATUS_REJECTED
    row.is_participating = False
    row.reject_reason = (payload.get('reject_reason') or '').strip()
    row.save(update_fields=['status', 'is_participating', 'reject_reason', 'updated_at'])


def _approve_subsidy(approval: Approval, reviewer: User, payload: dict[str, Any]) -> None:
    from subsidy.models import SubsidyProduct
    from subsidy.services import apply_filing_approved

    row = SubsidyProduct.objects.get(pk=approval.business_id)
    row.filing_status = SubsidyProduct.FILING_APPROVED
    row.filing_reject_reason = ''
    apply_filing_approved(row)
    row.save(
        update_fields=['filing_status', 'filing_reject_reason', 'subsidy_amount', 'updated_at'],
    )


def _reject_subsidy(approval: Approval, reviewer: User, payload: dict[str, Any]) -> None:
    from subsidy.models import SubsidyProduct

    row = SubsidyProduct.objects.get(pk=approval.business_id)
    row.filing_status = SubsidyProduct.FILING_REJECTED
    row.filing_reject_reason = (payload.get('reject_reason') or '').strip()
    row.subsidy_amount = 0
    row.save(update_fields=['filing_status', 'filing_reject_reason', 'subsidy_amount', 'updated_at'])


def _approve_promotion(approval: Approval, reviewer: User, payload: dict[str, Any]) -> None:
    from promotion.models import GroupBuyActivity, SeckillActivity

    model_map = {
        Approval.TYPE_SECKILL: SeckillActivity,
        Approval.TYPE_GROUPBUY: GroupBuyActivity,
    }
    model = model_map.get(approval.approval_type)
    if model is None:
        raise ValueError('不支持的促销审核类型')
    activity = model.objects.get(pk=approval.business_id)
    if activity.status not in {model.STATUS_PENDING, model.STATUS_REVIEWING}:
        raise ValueError('活动状态不可审核')
    from django.utils import timezone

    activity.status = model.STATUS_RUNNING
    activity.reject_reason = ''
    activity.approved_by = reviewer
    activity.approved_at = timezone.now()
    activity.save(update_fields=['status', 'reject_reason', 'approved_by', 'approved_at', 'updated_at'])


def _reject_promotion(approval: Approval, reviewer: User, payload: dict[str, Any]) -> None:
    from promotion.models import GroupBuyActivity, SeckillActivity

    model_map = {
        Approval.TYPE_SECKILL: SeckillActivity,
        Approval.TYPE_GROUPBUY: GroupBuyActivity,
    }
    model = model_map.get(approval.approval_type)
    if model is None:
        raise ValueError('不支持的促销审核类型')
    activity = model.objects.get(pk=approval.business_id)
    activity.status = model.STATUS_CANCELLED
    activity.reject_reason = (payload.get('reject_reason') or '').strip()
    activity.save(update_fields=['status', 'reject_reason', 'updated_at'])


APPROVE_HANDLERS: dict[str, Handler] = {
    Approval.TYPE_CLOSURE: _approve_closure,
    Approval.TYPE_TAG: _approve_tag,
    Approval.TYPE_SUBSIDY: _approve_subsidy,
    Approval.TYPE_SECKILL: _approve_promotion,
    Approval.TYPE_GROUPBUY: _approve_promotion,
}

REJECT_HANDLERS: dict[str, Handler] = {
    Approval.TYPE_CLOSURE: _reject_closure,
    Approval.TYPE_TAG: _reject_tag,
    Approval.TYPE_SUBSIDY: _reject_subsidy,
    Approval.TYPE_SECKILL: _reject_promotion,
    Approval.TYPE_GROUPBUY: _reject_promotion,
}
