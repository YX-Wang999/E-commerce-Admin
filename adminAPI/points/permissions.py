"""Points permission helpers."""

from rest_framework.permissions import BasePermission

from feedback.permissions import user_has_permission


class HasPointsRead(BasePermission):
    """Read points accounts and transactions."""

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'points:read')


class HasPointsAdjust(BasePermission):
    """Adjust customer points."""

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'points:adjust')


class HasPointsRule(BasePermission):
    """Manage points rules."""

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'points:rule')
