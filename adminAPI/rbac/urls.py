"""RBAC URL routes."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from rbac.views import MenuFlatListView, MenuViewSet, PermissionViewSet, RoleViewSet

router = DefaultRouter()
router.register('permissions', PermissionViewSet, basename='permission')
router.register('roles', RoleViewSet, basename='role')
router.register('menus', MenuViewSet, basename='menu')

urlpatterns = [
    path('menus/flat/', MenuFlatListView.as_view(), name='menu-flat'),
    path('', include(router.urls)),
]
