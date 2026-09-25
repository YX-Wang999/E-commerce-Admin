"""Seller auth serializers."""

from rest_framework import serializers

from tenants.models import Tenant, TenantStaff
from tenants.utils import resolve_tenant_by_login_key


def verify_seller_credentials(account: str, password: str) -> tuple[object | None, Tenant | None, TenantStaff | None]:
    """Validate seller login credentials and return (user, tenant, staff)."""
    from django.contrib.auth import authenticate
    from django.contrib.auth import get_user_model

    User = get_user_model()
    account = (account or '').strip()
    password = password or ''

    tenant = resolve_tenant_by_login_key(account, include_inactive=True)
    if tenant is None:
        return None, None, None

    user = None
    staff = None

    phone_user = User.objects.filter(username=tenant.contact_phone).first()
    if phone_user and phone_user.check_password(password):
        staff = (
            TenantStaff.objects.filter(tenant=tenant, user=phone_user)
            .select_related('tenant', 'user')
            .first()
        )
        if staff is not None:
            user = phone_user

    if staff is None:
        auth_user = authenticate(username=account, password=password)
        if auth_user is not None:
            staff = (
                TenantStaff.objects.filter(tenant=tenant, user=auth_user)
                .select_related('tenant', 'user')
                .first()
            )
            if staff is not None:
                user = auth_user

    if staff is None:
        email_user = User.objects.filter(email__iexact=account).first()
        if email_user is not None and email_user.check_password(password):
            staff = (
                TenantStaff.objects.filter(tenant=tenant, user=email_user)
                .select_related('tenant', 'user')
                .first()
            )
            if staff is not None:
                user = email_user

    if staff is None:
        for candidate in TenantStaff.objects.filter(tenant=tenant).select_related('user'):
            if candidate.user.check_password(password):
                user = candidate.user
                staff = candidate
                break

    if staff is None or user is None:
        return None, None, None

    if not staff.is_active:
        if staff.role == TenantStaff.ROLE_OWNER and tenant.status == Tenant.STATUS_ACTIVE:
            staff.is_active = True
            staff.save(update_fields=['is_active'])
        elif tenant.status == Tenant.STATUS_ACTIVE:
            return None, None, None
        return None, None, None

    return user, tenant, staff


class SellerLoginSerializer(serializers.Serializer):
    account = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, attrs):
        account = attrs['account'].strip()
        password = attrs['password']
        user, tenant, staff = verify_seller_credentials(account, password)

        if tenant is None:
            raise serializers.ValidationError('商户不存在，请检查名称或手机号')
        if user is None or staff is None:
            raise serializers.ValidationError('账号或密码错误')

        attrs['user'] = user
        attrs['tenant'] = tenant
        attrs['staff'] = staff
        return attrs
