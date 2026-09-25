"""Custom DRF permission classes."""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAdminRole(BasePermission):
    """Allow users with admin role or superuser flag."""

    message = '仅管理员可执行此操作'

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check whether the user has admin role."""
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.roles.filter(
            code__in=['super_admin', 'admin'],
            is_active=True,
        ).exists()


class IsSuperAdminRole(BasePermission):
    """Allow superuser or super_admin role only."""

    message = '仅超级管理员可执行此操作'

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check whether the user is a super administrator."""
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.roles.filter(code='super_admin', is_active=True).exists()
