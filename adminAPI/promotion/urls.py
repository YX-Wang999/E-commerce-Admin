"""Promotion URL configuration."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from promotion.views import (
    CouponViewSet,
    GroupBuyActivityViewSet,
    SeckillActivityViewSet,
    UserCouponViewSet,
)
from promotion.super_discount_views import SuperDiscountViewSet

router = DefaultRouter()
router.register('seckills', SeckillActivityViewSet, basename='seckill')
router.register('groupbuys', GroupBuyActivityViewSet, basename='groupbuy')
router.register('coupons', CouponViewSet, basename='coupon')
router.register('user-coupons', UserCouponViewSet, basename='user-coupon')
router.register('super-discounts', SuperDiscountViewSet, basename='super-discount')

urlpatterns = [
    path('', include(router.urls)),
]
