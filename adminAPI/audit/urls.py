"""Audit URL routes."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from audit.views import OperationLogViewSet

router = DefaultRouter()
router.register('logs', OperationLogViewSet, basename='operation-log')

urlpatterns = [
    path('', include(router.urls)),
]
