"""Mall customer promotion URL routes."""

from django.urls import path

from promotion.mall_views import (
    AvailableCouponsView,
    GroupBuyActivitiesView,
    GroupBuyJoinView,
    MyCouponsView,
    PublishCouponsView,
    ReceiveCouponView,
    SeckillActivitiesView,
    SeckillBuyView,
    SeckillProductsView,
)

coupon_urlpatterns = [
    path('my-coupons/', MyCouponsView.as_view(), name='coupons-my'),
    path('available/', AvailableCouponsView.as_view(), name='coupons-available'),
    path('publish/', PublishCouponsView.as_view(), name='coupons-publish'),
    path('<int:coupon_id>/receive/', ReceiveCouponView.as_view(), name='coupons-receive'),
]

seckill_urlpatterns = [
    path('activities/', SeckillActivitiesView.as_view(), name='seckill-activities'),
    path('products/', SeckillProductsView.as_view(), name='seckill-products'),
    path('<int:pk>/buy/', SeckillBuyView.as_view(), name='seckill-buy'),
]

groupbuy_urlpatterns = [
    path('activities/', GroupBuyActivitiesView.as_view(), name='groupbuy-activities'),
    path('<int:pk>/join/', GroupBuyJoinView.as_view(), name='groupbuy-join'),
]

urlpatterns = coupon_urlpatterns
