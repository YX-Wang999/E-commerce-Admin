"""Complaint URL routes."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from complaints.views import ComplaintViewSet
from complaints.stats_views import ComplaintStatsView

router = DefaultRouter()
router.register('', ComplaintViewSet, basename='complaint')

urlpatterns = [
    path('stats/', ComplaintStatsView.as_view(), name='complaint-stats'),
    path('', include(router.urls)),
]
