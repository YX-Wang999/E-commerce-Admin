"""Address API views."""

import logging

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from addresses.models import Address
from addresses.serializers import AddressSerializer
from common.response import error_response, success_response
from customers.permissions import IsCustomerAuthenticated

logger = logging.getLogger(__name__)


class AddressViewSet(viewsets.ModelViewSet):
    """CRUD for current mall customer's shipping addresses."""

    serializer_class = AddressSerializer
    permission_classes = [IsCustomerAuthenticated]

    def get_queryset(self):
        queryset = Address.objects.filter(customer=self.request.customer)
        tenant = getattr(self.request, 'tenant', None)
        if tenant is not None:
            queryset = queryset.filter(tenant=tenant)
        return queryset

    def perform_create(self, serializer):
        customer = self.request.customer
        tenant = getattr(self.request, 'tenant', None)
        queryset = self.get_queryset()
        is_default = serializer.validated_data.get('is_default', False)
        if not queryset.exists():
            is_default = True
        address = serializer.save(customer=customer, tenant=tenant, is_default=is_default)
        if is_default:
            queryset.exclude(pk=address.pk).update(is_default=False)

    def perform_update(self, serializer):
        instance = serializer.save()
        if serializer.validated_data.get('is_default'):
            self.get_queryset().exclude(pk=instance.pk).update(is_default=False)

    def list(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return success_response(data=self.get_serializer(self.get_object()).data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            self.perform_create(serializer)
        except Exception:
            logger.exception('Create address failed')
            return error_response('创建地址失败', code=50000, http_status=500)
        return success_response(data=serializer.data, message='创建成功', http_status=201)

    def update(self, request: Request, *args, **kwargs) -> Response:
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            self.perform_update(serializer)
        except Exception:
            logger.exception('Update address failed')
            return error_response('更新地址失败', code=50000, http_status=500)
        return success_response(data=serializer.data, message='更新成功')

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        was_default = instance.is_default
        instance.delete()
        if was_default:
            next_addr = self.get_queryset().first()
            if next_addr:
                next_addr.is_default = True
                next_addr.save(update_fields=['is_default', 'updated_at'])
        return success_response(message='删除成功')

    @action(detail=True, methods=['patch'], url_path='set-default')
    def set_default(self, request: Request, pk: int | None = None) -> Response:
        instance = self.get_object()
        self.get_queryset().update(is_default=False)
        instance.is_default = True
        instance.save(update_fields=['is_default', 'updated_at'])
        return success_response(data=self.get_serializer(instance).data, message='已设为默认地址')
