"""Customer feedback permission helpers."""

from rest_framework.permissions import BasePermission


def user_has_permission(user, code: str) -> bool:
    """Check whether user has a permission code."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.roles.filter(is_active=True, permissions__code=code).exists()


class HasFeedbackRead(BasePermission):
    """Read customer feedback."""

    message = '无客户留言查看权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'feedback:read')


class HasFeedbackReply(BasePermission):
    """Reply to and update customer feedback."""

    message = '无客户留言回复权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'feedback:reply')


class HasFeedbackDelete(BasePermission):
    """Delete customer feedback."""

    message = '无客户留言删除权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'feedback:delete')
