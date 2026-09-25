"""Promotion permission helpers."""

from rest_framework.permissions import BasePermission


def user_has_permission(user, code: str) -> bool:
    """Check whether user has a permission code."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.roles.filter(is_active=True, permissions__code=code).exists()


def user_role_codes(user) -> set[str]:
    """Return active role codes for user."""
    if not user or not user.is_authenticated:
        return set()
    return set(user.roles.filter(is_active=True).values_list('code', flat=True))


class HasPromotionRead(BasePermission):
    """Read seckill activities."""

    message = '无秒杀活动查看权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'promotion:read')


class HasPromotionCreate(BasePermission):
    """Create seckill activities."""

    message = '无秒杀活动创建权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'promotion:create')


class HasPromotionUpdate(BasePermission):
    """Update seckill activities."""

    message = '无秒杀活动编辑权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'promotion:update')


class HasPromotionSubmit(BasePermission):
    """Submit seckill for approval."""

    message = '无提交审核权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'promotion:submit')


class HasPromotionApprove(BasePermission):
    """Approve or reject seckill activities."""

    message = '无审批权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'promotion:approve')


class HasPromotionCancel(BasePermission):
    """Cancel seckill activities."""

    message = '无终止活动权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'promotion:cancel')


class HasCouponRead(BasePermission):
    """Read coupons."""

    message = '无优惠券查看权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'coupon:read')


class HasCouponCreate(BasePermission):
    """Create coupons."""

    message = '无优惠券创建权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'coupon:create')


class HasCouponUpdate(BasePermission):
    """Update coupons."""

    message = '无优惠券编辑权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'coupon:update')


class HasCouponPublish(BasePermission):
    """Publish or disable coupons."""

    message = '无优惠券发布/停用权限'

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'coupon:publish')
