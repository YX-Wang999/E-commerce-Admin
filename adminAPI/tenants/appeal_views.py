"""Tenant appeal API views."""

from django.db.models import Case, IntegerField, Q, Value, When
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from common.pagination import StandardPagination
from common.response import error_response, success_response
from tenants.models import TenantAppeal
from tenants.permissions import HasTenantAppeal
from tenants.serializers import TenantAppealReplySerializer, TenantAppealSerializer


class TenantAppealViewSet(viewsets.ReadOnlyModelViewSet):
    """Platform tenant appeal management."""

    queryset = TenantAppeal.objects.select_related('tenant', 'operator').all()
    serializer_class = TenantAppealSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated, HasTenantAppeal]

    def get_permissions(self):
        if self.action in ('reply',):
            return [IsAuthenticated(), HasTenantAppeal()]
        return [IsAuthenticated(), HasTenantAppeal()]

    def get_queryset(self):
        queryset = super().get_queryset()
        status = (self.request.query_params.get('status') or '').strip()
        keyword = (self.request.query_params.get('keyword') or '').strip()
        if status:
            queryset = queryset.filter(status=status)
        if keyword:
            queryset = queryset.filter(
                Q(tenant__name__icontains=keyword)
                | Q(tenant__contact_phone__icontains=keyword)
                | Q(title__icontains=keyword),
            )
        return queryset.annotate(
            status_order=Case(
                When(status=TenantAppeal.STATUS_PENDING, then=Value(0)),
                When(status=TenantAppeal.STATUS_PROCESSING, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            ),
        ).order_by('status_order', '-id')

    def list(self, request: Request, *args, **kwargs) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return success_response(data=self.get_serializer(queryset, many=True).data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return success_response(data=self.get_serializer(self.get_object()).data)

    @action(detail=True, methods=['post'], url_path='reply')
    def reply(self, request: Request, pk: int | None = None) -> Response:
        appeal = self.get_object()
        serializer = TenantAppealReplySerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message))
        from tenants.notify import record_platform_appeal_reply

        record_platform_appeal_reply(
            appeal=appeal,
            reply_content=serializer.validated_data['reply'],
            operator=request.user,
            status=serializer.validated_data['status'],
        )
        appeal.refresh_from_db()
        return success_response(
            data=TenantAppealSerializer(appeal).data,
            message='回复成功',
        )
