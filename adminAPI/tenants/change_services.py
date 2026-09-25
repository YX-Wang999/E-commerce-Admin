"""Tenant profile change submit and review."""

from __future__ import annotations

import json
from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from tenants.change_constants import (
    FIELD_LABELS,
    LOW_SENSITIVITY_FIELDS,
    PENDING_FIELD_MAP,
    REVIEW_REQUIRED_FIELDS,
)
from tenants.models import Tenant, TenantChangeLog
from tenants.name_rules import validate_tenant_name
from tenants.validators import check_tenant_availability

User = get_user_model()
PHONE_PATTERN = __import__('re').compile(r'^1[3-9]\d{9}$')


def _field_value(tenant: Tenant, field: str) -> str:
    value = getattr(tenant, field, '')
    if value is None:
        return ''
    if field == 'config':
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _validate_field_value(field: str, value: str, *, tenant: Tenant) -> str | None:
    value = (value or '').strip()
    if field == 'name':
        return validate_tenant_name(value)
    if field == 'contact_phone':
        if not PHONE_PATTERN.match(value):
            return '请输入正确的手机号'
        availability = check_tenant_availability(phone=value, exclude_id=tenant.id)
        if not availability['available']:
            return availability['errors'][0]
    if field == 'contact_email' and value and '@' not in value:
        return '邮箱格式不正确'
    if field in {'contact_name', 'legal_person'} and not value:
        return f'{FIELD_LABELS.get(field, field)}不能为空'
    return None


def get_tenant_pending_fields(tenant: Tenant) -> dict[str, str]:
    pending: dict[str, str] = {}
    for field, pending_attr in PENDING_FIELD_MAP.items():
        value = getattr(tenant, pending_attr, '') or ''
        if value:
            pending[field] = value
    return pending


def submit_tenant_profile_changes(
    *,
    tenant: Tenant,
    user: User,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Apply low-sensitivity updates immediately; queue others for review."""
    direct_updated: list[str] = []
    pending_submitted: list[str] = []
    errors: dict[str, str] = {}

    with transaction.atomic():
        locked = Tenant.objects.select_for_update().get(pk=tenant.pk)
        for field, raw in payload.items():
            if field not in LOW_SENSITIVITY_FIELDS and field not in REVIEW_REQUIRED_FIELDS:
                continue
            if field == 'config' and not isinstance(raw, dict):
                errors[field] = '配置格式不正确'
                continue
            value = raw if field == 'config' else str(raw or '').strip()
            if field != 'config' and value == _field_value(locked, field):
                continue

            error = _validate_field_value(field, value if field != 'config' else '', tenant=locked)
            if error:
                errors[field] = error
                continue

            if field in LOW_SENSITIVITY_FIELDS:
                old_display = _field_value(locked, field)
                setattr(locked, field, value)
                TenantChangeLog.objects.create(
                    tenant=locked,
                    field=field,
                    old_value=old_display,
                    new_value=value if field != 'config' else json.dumps(value, ensure_ascii=False),
                    status=TenantChangeLog.STATUS_APPROVED,
                    operator=user,
                    operator_type=TenantChangeLog.OPERATOR_TENANT,
                    reviewed_at=timezone.now(),
                )
                direct_updated.append(field)
                continue

            pending_attr = PENDING_FIELD_MAP[field]
            old_display = _field_value(locked, field)
            setattr(locked, pending_attr, value if field != 'config' else json.dumps(value, ensure_ascii=False))

            existing = TenantChangeLog.objects.filter(
                tenant=locked,
                field=field,
                status=TenantChangeLog.STATUS_PENDING,
            ).first()
            if existing:
                existing.old_value = old_display
                existing.new_value = value if field != 'config' else json.dumps(value, ensure_ascii=False)
                existing.operator = user
                existing.operator_type = TenantChangeLog.OPERATOR_TENANT
                existing.review_remark = ''
                existing.save(
                    update_fields=['old_value', 'new_value', 'operator', 'operator_type', 'review_remark'],
                )
            else:
                TenantChangeLog.objects.create(
                    tenant=locked,
                    field=field,
                    old_value=old_display,
                    new_value=value if field != 'config' else json.dumps(value, ensure_ascii=False),
                    status=TenantChangeLog.STATUS_PENDING,
                    operator=user,
                    operator_type=TenantChangeLog.OPERATOR_TENANT,
                )
            pending_submitted.append(field)

        if errors:
            transaction.set_rollback(True)
            return {'ok': False, 'errors': errors}

        locked.save()
        tenant.refresh_from_db()

    if pending_submitted:
        from tenants.change_notify import notify_platform_pending_change

        notify_platform_pending_change(tenant=tenant, fields=pending_submitted)

    return {
        'ok': True,
        'direct_updated': direct_updated,
        'pending_submitted': pending_submitted,
    }


def review_tenant_change(
    *,
    log: TenantChangeLog,
    reviewer: User,
    action: str,
    remark: str = '',
) -> TenantChangeLog:
    if log.status != TenantChangeLog.STATUS_PENDING:
        raise ValueError('该变更已处理')
    if action not in {'approve', 'reject'}:
        raise ValueError('无效审核操作')

    with transaction.atomic():
        tenant = Tenant.objects.select_for_update().get(pk=log.tenant_id)
        pending_attr = PENDING_FIELD_MAP.get(log.field)
        if action == 'approve':
            error = _validate_field_value(log.field, log.new_value, tenant=tenant)
            if error:
                raise ValueError(error)
            if pending_attr:
                setattr(tenant, log.field, getattr(tenant, pending_attr, '') or log.new_value)
                setattr(tenant, pending_attr, '')
            else:
                setattr(tenant, log.field, log.new_value)
            log.status = TenantChangeLog.STATUS_APPROVED
        else:
            if pending_attr:
                setattr(tenant, pending_attr, '')
            log.status = TenantChangeLog.STATUS_REJECTED

        log.reviewed_by = reviewer
        log.reviewed_at = timezone.now()
        log.review_remark = remark or ''
        log.save(
            update_fields=['status', 'reviewed_by', 'reviewed_at', 'review_remark'],
        )
        tenant.save()

    from tenants.change_notify import notify_merchant_change_reviewed

    notify_merchant_change_reviewed(log=log, approved=action == 'approve')
    return log
