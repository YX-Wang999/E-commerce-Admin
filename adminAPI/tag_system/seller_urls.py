"""Seller tag URL routes."""

from django.urls import path

from tag_system.seller_views import (
    SellerProductTagConfigListView,
    SellerTagConfigView,
    SellerTagListView,
)

urlpatterns = [
    path('tags/', SellerTagListView.as_view(), name='seller-tag-list'),
    path('tag-configs/', SellerTagConfigView.as_view(), name='seller-tag-config'),
    path('product-tag-configs/', SellerProductTagConfigListView.as_view(), name='seller-product-tag-config'),
]
