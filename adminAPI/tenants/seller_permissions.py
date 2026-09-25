"""Seller (tenant staff) permission helpers."""

from rest_framework.permissions import BasePermission

from tenants.seller_tenant import resolve_seller_tenant


def get_request_tenant(request):
    return resolve_seller_tenant(request) or getattr(request, 'tenant', None)


def is_tenant_staff_member(user, tenant) -> bool:
    if not user or not user.is_authenticated or tenant is None:
        return False
    if getattr(user, 'is_superuser', False):
        return True
    return user.tenant_staffs.filter(tenant=tenant, is_active=True).exists()


def is_tenant_staff_role(user, tenant, roles: set[str]) -> bool:
    if not is_tenant_staff_member(user, tenant):
        return False
    if getattr(user, 'is_superuser', False):
        return True
    return user.tenant_staffs.filter(tenant=tenant, is_active=True, role__in=roles).exists()


class IsTenantStaffMember(BasePermission):
    message = '非本店员工，无权访问'

    def has_permission(self, request, view) -> bool:
        return is_tenant_staff_member(request.user, get_request_tenant(request))


class IsTenantStaffManager(BasePermission):
    """Owner or manager."""

    message = '需要店长或管理员权限'

    def has_permission(self, request, view) -> bool:
        tenant = get_request_tenant(request)
        return is_tenant_staff_role(
            request.user,
            tenant,
            {'owner', 'manager'},
        )
