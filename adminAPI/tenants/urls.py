"""Tenant URL routes."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from tenants.views import TenantStaffViewSet, TenantViewSet
from tenants.appeal_views import TenantAppealViewSet

router = DefaultRouter()
router.register('tenants', TenantViewSet, basename='tenant')
router.register('tenant-staffs', TenantStaffViewSet, basename='tenant-staff')
router.register('tenant-appeals', TenantAppealViewSet, basename='tenant-appeal')

urlpatterns = [
    path('', include(router.urls)),
]
