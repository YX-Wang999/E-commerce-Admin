"""Subsidy permission helpers."""

from rest_framework.permissions import BasePermission

from promotion.permissions import user_has_permission


class HasSubsidyRead(BasePermission):
    message = '无国补查看权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'subsidy:read')


class HasSubsidyCreate(BasePermission):
    message = '无国补创建权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'subsidy:create')


class HasSubsidyUpdate(BasePermission):
    message = '无国补编辑权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'subsidy:update')


class HasSubsidyApprove(BasePermission):
    message = '无国补审核权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'subsidy:approve')
