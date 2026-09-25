"""Tenant helpers."""

from __future__ import annotations

import re

from django.contrib.auth import get_user_model
from django.db.models import Max
from django.utils import timezone

PHONE_PATTERN = re.compile(r'^1[3-9]\d{9}$')


def generate_store_code() -> str:
    """Generate unique code: STORE + YYYYMMDD + 4-digit sequence."""
    from tenants.models import Tenant

    date_str = timezone.localdate().strftime('%Y%m%d')
    prefix = f'STORE{date_str}'
    latest = (
        Tenant.objects.filter(code__startswith=prefix)
        .aggregate(max_code=Max('code'))
        .get('max_code')
    )
    if latest and latest.startswith(prefix) and len(latest) >= len(prefix) + 4:
        try:
            seq = int(latest[len(prefix):]) + 1
        except ValueError:
            seq = Tenant.objects.filter(code__startswith=prefix).count() + 1
    else:
        seq = Tenant.objects.filter(code__startswith=prefix).count() + 1

    for offset in range(seq, seq + 1000):
        code = f'{prefix}{str(offset).zfill(4)}'
        if not Tenant.objects.filter(code=code).exists():
            return code
    raise ValueError('无法生成商户编码')


def resolve_tenant_by_login_key(key: str, *, include_inactive: bool = False):
    """Find tenant by contact phone, shop name, code, or owner username."""
    from tenants.models import Tenant, TenantStaff

    value = (key or '').strip()
    if not value:
        return None
    queryset = Tenant.objects.all()
    if not include_inactive:
        queryset = queryset.filter(is_active=True)

    tenant = queryset.filter(contact_phone=value).first()
    if tenant is not None:
        return tenant

    tenant = queryset.filter(name__iexact=value).first()
    if tenant is not None:
        return tenant

    tenant = queryset.filter(code__iexact=value).first()
    if tenant is not None:
        return tenant

    if PHONE_PATTERN.match(value):
        User = get_user_model()
        user = User.objects.filter(username=value).first()
        if user is not None:
            staff_qs = TenantStaff.objects.filter(user=user).select_related('tenant')
            if not include_inactive:
                staff_qs = staff_qs.filter(tenant__is_active=True)
            staff = staff_qs.first()
            if staff is not None:
                return staff.tenant

    return None


def is_orphan_seller_user(user) -> bool:
    """Seller portal account with no tenant staff binding."""
    if user is None:
        return False
    if not PHONE_PATTERN.match(str(user.username or '').strip()):
        return False
    if user.is_staff or user.is_superuser:
        return False
    if user.roles.exists():
        return False
    return not user.tenant_staffs.exists()


def cleanup_orphan_seller_user(user) -> bool:
    """Delete seller-only user left after tenant removal."""
    if not is_orphan_seller_user(user):
        return False
    user.delete()
    return True


def delete_tenant_with_staff_users(tenant) -> None:
    """Delete tenant and remove seller users that only belonged to it."""
    from tenants.models import TenantStaff

    user_ids = list(
        TenantStaff.objects.filter(tenant=tenant)
        .values_list('user_id', flat=True)
        .distinct(),
    )
    tenant.delete()
    User = get_user_model()
    for user_id in user_ids:
        user = User.objects.filter(pk=user_id).first()
        if user is not None:
            cleanup_orphan_seller_user(user)


def resolve_or_reuse_seller_user(*, phone: str, password: str, contact_name: str, email: str):
    """Create seller user or reuse/delete orphan account for the same phone."""
    User = get_user_model()
    existing = User.objects.filter(username=phone).first()
    if existing is None:
        return User.objects.create_user(
            username=phone,
            password=password,
            nickname=contact_name,
            email=email,
            is_active=True,
        )
    if existing.tenant_staffs.exists():
        raise ValueError('该手机号已注册，请直接登录')
    existing.delete()
    return User.objects.create_user(
        username=phone,
        password=password,
        nickname=contact_name,
        email=email,
        is_active=True,
    )
