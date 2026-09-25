"""Address URL configuration."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from addresses.views import AddressViewSet

router = DefaultRouter()
router.register('addresses', AddressViewSet, basename='address')

urlpatterns = [
    path('', include(router.urls)),
]
