"""System setting views."""

import logging

from rest_framework import viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination
from common.response import error_response, success_response
from system.models import SystemSetting
from system.role_display_names import (
    ROLE_DISPLAY_NAMES_KEY,
    get_merged_names,
    get_role_display_payload,
    save_role_display_names,
)
from system.serializers import SystemSettingSerializer

logger = logging.getLogger(__name__)


class SystemSettingViewSet(viewsets.ModelViewSet):
    """System setting CRUD viewset."""

    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def list(self, request: Request, *args, **kwargs) -> Response:
        """List settings."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        """Retrieve a setting."""
        serializer = self.get_serializer(self.get_object())
        return success_response(data=serializer.data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create a setting."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Create setting failed')
            return error_response('创建配置失败', code=50000, http_status=500)
        return success_response(data=self.get_serializer(instance).data, message='创建成功')

    def update(self, request: Request, *args, **kwargs) -> Response:
        """Update a setting."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Update setting failed')
            return error_response('更新配置失败', code=50000, http_status=500)
        return success_response(data=self.get_serializer(instance).data, message='更新成功')

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Delete a setting."""
        try:
            self.get_object().delete()
        except Exception:
            logger.exception('Delete setting failed')
            return error_response('删除配置失败', code=50000, http_status=500)
        return success_response(message='删除成功')


class RoleDisplayNamesView(APIView):
    """Get / update custom role display names (multi-locale)."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return success_response(data=get_role_display_payload())

    def put(self, request: Request) -> Response:
        try:
            merged = save_role_display_names(request.data)
        except ValueError as exc:
            return error_response(str(exc))
        except Exception:
            logger.exception('Save role display names failed')
            return error_response('保存失败', code=50000, http_status=500)
        return success_response(
            data={'merged': merged, **get_role_display_payload()},
            message='保存成功',
        )


class PublicSystemSettingView(APIView):
    """Public system settings for layout."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return key-value map of settings."""
        settings_map = {
            item.key: item.value
            for item in SystemSetting.objects.all()
        }
        settings_map[ROLE_DISPLAY_NAMES_KEY] = get_merged_names()
        return success_response(data=settings_map)
