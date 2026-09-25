"""Product URL routes."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.views import BrandViewSet, CategoryViewSet, InventoryLogViewSet, ProductViewSet

router = DefaultRouter()
router.register('inventory-logs', InventoryLogViewSet, basename='inventory-log')
router.register('categories', CategoryViewSet, basename='category')
router.register('brands', BrandViewSet, basename='brand')
router.register('', ProductViewSet, basename='product')

urlpatterns = [
    path('', include(router.urls)),
]
