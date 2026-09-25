"""System URL routes."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from system.views import PublicSystemSettingView, RoleDisplayNamesView, SystemSettingViewSet

router = DefaultRouter()
router.register('settings', SystemSettingViewSet, basename='system-setting')

urlpatterns = [
    path('settings/public/', PublicSystemSettingView.as_view(), name='system-setting-public'),
    path(
        'settings/role-display-names/',
        RoleDisplayNamesView.as_view(),
        name='system-role-display-names',
    ),
    path('', include(router.urls)),
]
