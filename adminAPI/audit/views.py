"""Audit views."""

import logging

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from audit.models import OperationLog
from audit.serializers import OperationLogSerializer
from accounts.scopes import filter_audit_logs_by_scope
from common.pagination import StandardPagination
from common.response import success_response

logger = logging.getLogger(__name__)


class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Operation log read-only viewset."""

    queryset = OperationLog.objects.select_related('user').all()
    serializer_class = OperationLogSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        locale = self.request.query_params.get('locale') or self.request.headers.get('Accept-Language', 'zh-CN')
        context['locale'] = locale.split(',')[0].strip() or 'zh-CN'
        return context

    def get_queryset(self):
        """Filter logs by query params and role data scope."""
        queryset = filter_audit_logs_by_scope(
            super().get_queryset(),
            self.request.user,
        )
        username = self.request.query_params.get('username')
        module = self.request.query_params.get('module')
        action = self.request.query_params.get('action')
        if username:
            queryset = queryset.filter(username__icontains=username)
        if module:
            queryset = queryset.filter(module__icontains=module)
        if action:
            queryset = queryset.filter(action=action)
        return queryset

    def list(self, request: Request, *args, **kwargs) -> Response:
        """List operation logs."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        """Retrieve an operation log."""
        serializer = self.get_serializer(self.get_object())
        return success_response(data=serializer.data)
