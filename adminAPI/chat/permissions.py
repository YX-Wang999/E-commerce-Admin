"""Chat permission helpers."""

from rest_framework.permissions import BasePermission

from feedback.permissions import user_has_permission

CHAT_STAFF_PERMISSIONS = {'chat:read', 'chat:reply', 'chat:assign', 'chat:close'}


def is_admin_user(user) -> bool:
    """Whether principal is a backend admin User (not mall CustomerAuthUser)."""
    return getattr(user, 'roles', None) is not None


def is_chat_staff(user) -> bool:
    """Whether user can access the platform support workbench."""
    if not user or not user.is_authenticated:
        return False
    if not is_admin_user(user):
        return False
    if getattr(user, 'is_superuser', False):
        return True
    return user.roles.filter(
        is_active=True,
        permissions__code__in=CHAT_STAFF_PERMISSIONS,
    ).exists()


def is_tenant_chat_staff(user, tenant) -> bool:
    """Whether user can access the merchant-side chat workbench."""
    if not user or not user.is_authenticated or tenant is None:
        return False
    from tenants.seller_permissions import is_tenant_staff_member

    return is_tenant_staff_member(user, tenant)


def can_access_chat_workbench(user, request) -> bool:
    """Platform CS staff or active tenant staff may use chat APIs."""
    if is_chat_staff(user):
        return True
    tenant = getattr(request, 'tenant', None)
    return is_tenant_chat_staff(user, tenant)


def can_assign_conversations(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if not is_admin_user(user):
        return False
    if getattr(user, 'is_superuser', False):
        return True
    return user_has_permission(user, 'chat:assign')


class HasChatRead(BasePermission):
    message = '无在线客服查看权限'

    def has_permission(self, request, view) -> bool:
        return can_access_chat_workbench(request.user, request)


class HasChatReply(BasePermission):
    message = '无在线客服回复权限'

    def has_permission(self, request, view) -> bool:
        if not is_admin_user(request.user):
            return False
        if getattr(request.user, 'is_superuser', False):
            return True
        return user_has_permission(request.user, 'chat:reply')


class HasChatAssign(BasePermission):
    message = '无会话分配权限'

    def has_permission(self, request, view) -> bool:
        return can_assign_conversations(request.user)
