"""Complaint permission helpers."""

from rest_framework.permissions import BasePermission

from feedback.permissions import user_has_permission
from tenants.seller_permissions import is_tenant_staff_member


def user_is_platform_complaint_staff(user) -> bool:
    if getattr(user, 'is_superuser', False):
        return True
    return user_has_permission(user, 'complaint:read')


class IsCustomerComplaintUser(BasePermission):
    def has_permission(self, request, view):
        return getattr(request, 'customer', None) is not None


class IsPlatformComplaintStaff(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'is_superuser', False):
            return True
        action = getattr(view, 'action', None)
        if action in ('platform_review',):
            return user_has_permission(user, 'complaint:review')
        if action in ('close',):
            return user_has_permission(user, 'complaint:close') or user_has_permission(user, 'complaint:review')
        return user_is_platform_complaint_staff(user)


class IsTenantComplaintStaff(BasePermission):
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        tenant = getattr(request, 'tenant', None)
        return (
            user
            and user.is_authenticated
            and tenant is not None
            and is_tenant_staff_member(user, tenant)
        )


class IsCustomerOrStaff(BasePermission):
    def has_permission(self, request, view):
        if getattr(request, 'customer', None) is not None:
            return True
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        if getattr(request, 'tenant', None) is not None:
            return is_tenant_staff_member(user, request.tenant)
        return user_is_platform_complaint_staff(user)
