"""Admin tag URL routes."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from tag_system.admin_views import (
    AdminProductTagConfigView,
    AdminTagCategoryViewSet,
    AdminTagViewSet,
    AdminTenantTagConfigViewSet,
)

router = DefaultRouter()
router.register('categories', AdminTagCategoryViewSet, basename='admin-tag-category')
router.register('tags', AdminTagViewSet, basename='admin-tag')
router.register('tenant-tag-configs', AdminTenantTagConfigViewSet, basename='admin-tenant-tag-config')

urlpatterns = [
    path('product-tag-configs/', AdminProductTagConfigView.as_view(), name='admin-product-tag-config'),
    path('', include(router.urls)),
]
