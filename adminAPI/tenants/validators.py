"""Tenant field availability checks."""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model

from tenants.models import Tenant
from tenants.name_rules import validate_tenant_name
from tenants.utils import is_orphan_seller_user


def check_tenant_availability(
    *,
    exclude_id: int | None = None,
    code: str | None = None,
    phone: str | None = None,
    name: str | None = None,
    contact_name: str | None = None,
    for_apply: bool = False,
) -> dict[str, Any]:
    """Validate tenant fields before save."""
    result: dict[str, Any] = {'available': True, 'errors': [], 'warnings': []}

    if code:
        queryset = Tenant.objects.filter(code__iexact=str(code).strip())
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        if queryset.exists():
            result['available'] = False
            result['errors'].append('商户编码已存在')

    if phone:
        phone_value = str(phone).strip()
        queryset = Tenant.objects.filter(contact_phone=phone_value)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        if queryset.exists():
            result['available'] = False
            result['errors'].append('该联系电话已被其他商户使用')
        elif for_apply:
            user_error = _phone_user_registration_error(phone_value)
            if user_error:
                result['available'] = False
                result['errors'].append(user_error)

    if name:
        name_value = str(name).strip()
        format_error = validate_tenant_name(name_value)
        if format_error:
            result['available'] = False
            result['errors'].append(format_error)
        else:
            queryset = Tenant.objects.filter(name__iexact=name_value)
            if exclude_id:
                queryset = queryset.exclude(id=exclude_id)
            duplicate = queryset.first()
            if duplicate:
                if duplicate.status == Tenant.STATUS_ACTIVE:
                    result['warnings'].append(
                        f'已有审核通过的商户使用名称「{duplicate.name}」，继续提交可能让客户混淆，是否确认使用？',
                    )
                else:
                    result['available'] = False
                    result['errors'].append('该店铺名称已被使用')

    if contact_name:
        queryset = Tenant.objects.filter(contact_name__iexact=str(contact_name).strip())
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        if queryset.exists():
            result['available'] = False
            result['errors'].append('该联系人已被其他商户使用')

    return result


def _phone_user_registration_error(phone: str) -> str | None:
    User = get_user_model()
    user = User.objects.filter(username=phone).first()
    if user is None or is_orphan_seller_user(user):
        return None
    return '该手机号已注册，请直接登录'
