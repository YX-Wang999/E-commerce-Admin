"""RBAC views."""

import logging

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination
from common.response import error_response, success_response
from rbac.models import Menu, Permission, Role
from rbac.serializers import (
    MenuSerializer,
    PermissionSerializer,
    RoleSerializer,
)
from rbac.utils import build_menu_tree

logger = logging.getLogger(__name__)


class PermissionViewSet(viewsets.ModelViewSet):
    """Permission CRUD viewset."""

    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def list(self, request: Request, *args, **kwargs) -> Response:
        """List permissions."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        """Retrieve a permission."""
        serializer = self.get_serializer(self.get_object())
        return success_response(data=serializer.data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create a permission."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Create permission failed')
            return error_response('创建权限失败', code=50000, http_status=500)
        return success_response(data=self.get_serializer(instance).data, message='创建成功')

    def update(self, request: Request, *args, **kwargs) -> Response:
        """Update a permission."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Update permission failed')
            return error_response('更新权限失败', code=50000, http_status=500)
        return success_response(data=self.get_serializer(instance).data, message='更新成功')

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Delete a permission."""
        try:
            self.get_object().delete()
        except Exception:
            logger.exception('Delete permission failed')
            return error_response('删除权限失败', code=50000, http_status=500)
        return success_response(message='删除成功')


class RoleViewSet(viewsets.ModelViewSet):
    """Role CRUD viewset."""

    queryset = Role.objects.prefetch_related('permissions', 'menus').all()
    serializer_class = RoleSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def list(self, request: Request, *args, **kwargs) -> Response:
        """List roles."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        """Retrieve a role."""
        serializer = self.get_serializer(self.get_object())
        return success_response(data=serializer.data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create a role."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Create role failed')
            return error_response('创建角色失败', code=50000, http_status=500)
        return success_response(data=self.get_serializer(instance).data, message='创建成功')

    def update(self, request: Request, *args, **kwargs) -> Response:
        """Update a role."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Update role failed')
            return error_response('更新角色失败', code=50000, http_status=500)
        return success_response(data=self.get_serializer(instance).data, message='更新成功')

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Delete a role."""
        try:
            self.get_object().delete()
        except Exception:
            logger.exception('Delete role failed')
            return error_response('删除角色失败', code=50000, http_status=500)
        return success_response(message='删除成功')


class MenuViewSet(viewsets.ModelViewSet):
    """Menu CRUD viewset."""

    queryset = Menu.objects.select_related('permission', 'parent').all()
    serializer_class = MenuSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def list(self, request: Request, *args, **kwargs) -> Response:
        """List menus as tree."""
        queryset = self.filter_queryset(self.get_queryset())
        flat_menus = list(
            queryset.order_by('sort_order', 'id').values(
                'id',
                'parent_id',
                'title',
                'name',
                'path',
                'component',
                'icon',
                'menu_type',
                'permission_id',
                'sort_order',
                'is_visible',
                'is_active',
            ),
        )
        normalized = [
            {
                'id': item['id'],
                'parent': item['parent_id'],
                'title': item['title'],
                'name': item['name'],
                'path': item['path'],
                'component': item['component'],
                'icon': item['icon'],
                'menu_type': item['menu_type'],
                'permission': item['permission_id'],
                'sort_order': item['sort_order'],
                'is_visible': item['is_visible'],
                'is_active': item['is_active'],
            }
            for item in flat_menus
        ]
        tree = build_menu_tree(normalized)
        return success_response(data=tree)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        """Retrieve a menu."""
        serializer = self.get_serializer(self.get_object())
        return success_response(data=serializer.data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create a menu."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Create menu failed')
            return error_response('创建菜单失败', code=50000, http_status=500)
        return success_response(data=self.get_serializer(instance).data, message='创建成功')

    def update(self, request: Request, *args, **kwargs) -> Response:
        """Update a menu."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Update menu failed')
            return error_response('更新菜单失败', code=50000, http_status=500)
        return success_response(data=self.get_serializer(instance).data, message='更新成功')

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Delete a menu."""
        try:
            self.get_object().delete()
        except Exception:
            logger.exception('Delete menu failed')
            return error_response('删除菜单失败', code=50000, http_status=500)
        return success_response(message='删除成功')


class MenuFlatListView(APIView):
    """Flat menu list for role assignment."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return flat menu list."""
        menus = Menu.objects.filter(is_active=True).order_by('sort_order', 'id')
        serializer = MenuSerializer(menus, many=True)
        return success_response(data=serializer.data)
