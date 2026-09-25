"""Public super discount routes."""

from django.urls import path

from promotion.super_discount_views import SuperDiscountActiveView

urlpatterns = [
    path('active/', SuperDiscountActiveView.as_view(), name='super-discount-active'),
]
