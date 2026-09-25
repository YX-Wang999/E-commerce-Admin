"""Tenant status and appeal helpers."""

from __future__ import annotations

from django.conf import settings

from tenants.models import Tenant, TenantSuspensionLog


def get_platform_contact() -> dict[str, str]:
    return {
        'phone': getattr(settings, 'PLATFORM_SERVICE_PHONE', '400-888-8888'),
        'email': getattr(settings, 'PLATFORM_SERVICE_EMAIL', 'service@platform.com'),
    }


def log_suspension_action(
    tenant: Tenant,
    *,
    action: str,
    reason: str,
    operator,
    detail: dict | None = None,
) -> TenantSuspensionLog:
    return TenantSuspensionLog.objects.create(
        tenant=tenant,
        action=action,
        reason=reason,
        detail=detail or {},
        operator=operator,
    )


def get_last_suspend_log(tenant: Tenant) -> TenantSuspensionLog | None:
    return (
        tenant.suspension_logs.filter(action=TenantSuspensionLog.ACTION_SUSPEND)
        .order_by('-id')
        .first()
    )


def build_tenant_login_block(tenant: Tenant) -> dict | None:
    """Return login block payload when tenant status forbids login."""
    contact = get_platform_contact()

    if tenant.status == Tenant.STATUS_PENDING:
        return {
            'message': '入驻审核中，请等待审核结果',
            'data': {
                'status': 'pending',
                'hint': '平台将在 1-3 个工作日内完成审核',
                'contact': contact,
            },
        }

    if tenant.status == Tenant.STATUS_SUSPENDED:
        last_log = get_last_suspend_log(tenant)
        return {
            'message': '账户已被暂停',
            'data': {
                'status': 'suspended',
                'reason': last_log.reason if last_log else '违反平台规则',
                'detail': last_log.detail if last_log else {},
                'suspended_at': last_log.created_at.isoformat() if last_log else None,
                'contact': contact,
            },
        }

    if tenant.status == Tenant.STATUS_CLOSED:
        last_log = (
            tenant.suspension_logs.filter(action=TenantSuspensionLog.ACTION_CLOSE)
            .order_by('-id')
            .first()
        )
        return {
            'message': '账户已关闭',
            'data': {
                'status': 'closed',
                'reason': last_log.reason if last_log else '账户已永久关闭',
                'detail': last_log.detail if last_log else {},
                'contact': contact,
            },
        }

    return None
