"""Announcement URL routes."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from announcement.views import (
    AnnouncementBannerView,
    AnnouncementLatestView,
    AnnouncementViewSet,
    AnnouncementVisibleView,
)

router = DefaultRouter()
router.register('', AnnouncementViewSet, basename='announcement')

urlpatterns = [
    path('banners/', AnnouncementBannerView.as_view(), name='announcement-banners'),
    path('latest/', AnnouncementLatestView.as_view(), name='announcement-latest'),
    path('visible/', AnnouncementVisibleView.as_view(), name='announcement-visible'),
    path('', include(router.urls)),
]
