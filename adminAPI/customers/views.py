"""Customer views."""

import logging

from django.db import models
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from common.pagination import StandardPagination
from common.response import error_response, success_response
from common.tenant import TenantViewSetMixin
from customers.models import Customer
from customers.serializers import CustomerSerializer

logger = logging.getLogger(__name__)


class CustomerViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """Customer CRUD viewset."""

    queryset = Customer.objects.select_related('member_profile__current_level').all()
    serializer_class = CustomerSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        queryset = super().get_queryset()
        keyword = self.request.query_params.get('keyword')
        level = self.request.query_params.get('level')
        if keyword:
            queryset = queryset.filter(
                models.Q(name__icontains=keyword)
                | models.Q(nickname__icontains=keyword)
                | models.Q(phone__icontains=keyword)
            )
        if level:
            queryset = queryset.filter(level=level)
        return queryset

    def list(self, request: Request, *args, **kwargs) -> Response:
        """List customers."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        """Retrieve customer."""
        return success_response(data=self.get_serializer(self.get_object()).data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create customer."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Create customer failed')
            return error_response('创建失败', code=50000, http_status=500)
        return success_response(
            data=self.get_serializer(instance).data,
            message='创建成功',
            http_status=status.HTTP_201_CREATED,
        )

    def update(self, request: Request, *args, **kwargs) -> Response:
        """Update customer."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Update customer failed')
            return error_response('更新失败', code=50000, http_status=500)
        return success_response(data=self.get_serializer(instance).data, message='更新成功')

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Delete customer when no orders exist (for test account cleanup)."""
        instance = self.get_object()
        if instance.orders.exists():
            return error_response('该用户存在订单，无法删除，请使用禁用')
        try:
            instance.delete()
        except Exception:
            logger.exception('Delete customer failed')
            return error_response('删除失败', code=50000, http_status=500)
        return success_response(message='删除成功')
