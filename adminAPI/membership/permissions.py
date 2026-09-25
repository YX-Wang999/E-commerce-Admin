"""Membership permission helpers."""

from rest_framework.permissions import BasePermission

from promotion.permissions import user_has_permission


class HasMembershipRead(BasePermission):
    message = '无会员等级查看权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'membership:read')


class HasMembershipManage(BasePermission):
    message = '无会员等级管理权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'membership:manage')
