"""Admin subsidy URL routes."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from subsidy.admin_views import (
    SubsidyOrderAdminViewSet,
    SubsidyPolicyViewSet,
    SubsidyProductAdminViewSet,
    SubsidyStatsView,
)

router = DefaultRouter()
router.register('policies', SubsidyPolicyViewSet, basename='admin-subsidy-policy')
router.register('filings', SubsidyProductAdminViewSet, basename='admin-subsidy-filing')
router.register('orders', SubsidyOrderAdminViewSet, basename='admin-subsidy-order')

urlpatterns = [
    path('stats/', SubsidyStatsView.as_view(), name='admin-subsidy-stats'),
    path('', include(router.urls)),
]
