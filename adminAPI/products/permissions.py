"""Product permissions."""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class CanViewInventoryLog(BasePermission):
    """Allow inventory log access for authorized roles."""

    message = '无库存流水查看权限'

    def has_permission(self, request, view) -> bool:
        """Check user role or permission."""
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        role_codes = set(user.roles.filter(is_active=True).values_list('code', flat=True))
        if role_codes & {'super_admin', 'ops_manager', 'warehouse_manager'}:
            return True

        permission_codes = set(
            user.roles.filter(is_active=True).values_list('permissions__code', flat=True),
        )
        return 'inventory:read' in permission_codes


class CanManageCategory(BasePermission):
    """Allow category mutations for admin leadership roles only."""

    message = '无分类管理权限'

    MANAGE_ROLES = {'super_admin', 'ops_director', 'ops_manager'}

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        if user.is_superuser:
            return True
        role_codes = set(user.roles.filter(is_active=True).values_list('code', flat=True))
        return bool(role_codes & self.MANAGE_ROLES)
