"""Shop rating URL routes."""

from django.urls import path

from shop_rating.admin_views import (
    AdminRatingAdjustmentListView,
    AdminRatingAdjustmentReviewView,
    AdminShopRatingAlertView,
    AdminShopRatingListView,
    AdminShopRatingTrendView,
)
from shop_rating.mall_views import MallTenantRatingView, MallTenantReviewsView
from shop_rating.seller_views import (
    SellerRatingAdjustmentRequestView,
    SellerShopRatingReviewsView,
    SellerShopRatingView,
)

urlpatterns = [
    path('seller/shop-rating/', SellerShopRatingView.as_view(), name='seller-shop-rating'),
    path('seller/shop-rating/reviews/', SellerShopRatingReviewsView.as_view(), name='seller-shop-rating-reviews'),
    path(
        'seller/shop-rating/adjustment-requests/',
        SellerRatingAdjustmentRequestView.as_view(),
        name='seller-shop-rating-adjustment',
    ),
    path('admin/shop-ratings/', AdminShopRatingListView.as_view(), name='admin-shop-ratings'),
    path('admin/shop-ratings/trends/', AdminShopRatingTrendView.as_view(), name='admin-shop-rating-trends'),
    path('admin/shop-ratings/alerts/', AdminShopRatingAlertView.as_view(), name='admin-shop-rating-alerts'),
    path(
        'admin/shop-ratings/adjustment-requests/',
        AdminRatingAdjustmentListView.as_view(),
        name='admin-shop-rating-adjustments',
    ),
    path(
        'admin/shop-ratings/adjustment-requests/<int:pk>/review/',
        AdminRatingAdjustmentReviewView.as_view(),
        name='admin-shop-rating-adjustment-review',
    ),
    path('customer/tenants/<int:tenant_id>/rating/', MallTenantRatingView.as_view(), name='mall-tenant-rating'),
    path('customer/tenants/<int:tenant_id>/reviews/', MallTenantReviewsView.as_view(), name='mall-tenant-reviews'),
]
