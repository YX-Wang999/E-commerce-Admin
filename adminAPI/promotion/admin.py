"""Promotion admin."""

from django.contrib import admin

from promotion.models import Coupon, GroupBuyActivity, GroupOrder, SeckillActivity, UserCoupon


@admin.register(SeckillActivity)
class SeckillActivityAdmin(admin.ModelAdmin):
    """Admin for seckill activities."""

    list_display = ['id', 'name', 'status', 'start_time', 'end_time', 'created_by', 'created_at']
    list_filter = ['status']
    search_fields = ['name']
    filter_horizontal = ['products']


@admin.register(GroupBuyActivity)
class GroupBuyActivityAdmin(admin.ModelAdmin):
    """Admin for group buy activities."""

    list_display = ['id', 'name', 'product', 'status', 'group_size', 'start_time', 'end_time']
    list_filter = ['status']
    search_fields = ['name']


@admin.register(GroupOrder)
class GroupOrderAdmin(admin.ModelAdmin):
    """Admin for group orders."""

    list_display = ['id', 'activity', 'order', 'captain', 'status', 'expired_at']
    list_filter = ['status']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """Admin for coupons."""

    list_display = ['id', 'name', 'coupon_type', 'status', 'total_quantity', 'created_at']
    list_filter = ['status', 'coupon_type']
    search_fields = ['name']
    filter_horizontal = ['applicable_products']


@admin.register(UserCoupon)
class UserCouponAdmin(admin.ModelAdmin):
    """Admin for user coupons."""

    list_display = ['id', 'code', 'coupon', 'user', 'status', 'received_at', 'expired_at']
    list_filter = ['status']
