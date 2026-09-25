"""Tenant management permission helpers."""

from rest_framework.permissions import BasePermission


def user_has_permission(user, code: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    if getattr(user, 'is_superuser', False):
        return True
    return user.roles.filter(is_active=True, permissions__code=code).exists()


class HasTenantView(BasePermission):
    message = '无商户查看权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'tenant:view')


class HasTenantCreate(BasePermission):
    message = '无商户新增权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'tenant:create')


class HasTenantApprove(BasePermission):
    message = '无商户审核权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'tenant:approve')


class HasTenantSuspend(BasePermission):
    message = '无商户暂停/恢复权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'tenant:suspend')


class HasTenantDelete(BasePermission):
    message = '无商户删除权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'tenant:delete')


class HasTenantAppeal(BasePermission):
    message = '无申诉处理权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'tenant:appeal')


def user_can_view_tenant_changes(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if getattr(user, 'is_superuser', False):
        return True
    role_codes = set(user.roles.filter(is_active=True).values_list('code', flat=True))
    if role_codes & {'ops_director', 'ops_manager'}:
        return True
    return user_has_permission(user, 'tenant:change:view')


def user_can_review_tenant_changes(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if getattr(user, 'is_superuser', False):
        return True
    role_codes = set(user.roles.filter(is_active=True).values_list('code', flat=True))
    if 'ops_director' in role_codes:
        return True
    return user_has_permission(user, 'tenant:change:review')


class HasTenantChangeView(BasePermission):
    message = '无商户变更查看权限'

    def has_permission(self, request, view) -> bool:
        return user_can_view_tenant_changes(request.user)


class HasTenantChangeReview(BasePermission):
    message = '无商户变更审核权限'

    def has_permission(self, request, view) -> bool:
        return user_can_review_tenant_changes(request.user)
