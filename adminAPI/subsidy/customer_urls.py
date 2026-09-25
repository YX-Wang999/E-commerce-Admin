"""Customer subsidy URL routes."""

from django.urls import path

from subsidy.customer_views import (
    CustomerSubsidyCalculateView,
    CustomerSubsidyEligibilityView,
    CustomerSubsidyProductListView,
)

urlpatterns = [
    path('products/', CustomerSubsidyProductListView.as_view(), name='customer-subsidy-products'),
    path('calculate/', CustomerSubsidyCalculateView.as_view(), name='customer-subsidy-calculate'),
    path('eligibility/', CustomerSubsidyEligibilityView.as_view(), name='customer-subsidy-eligibility'),
]
