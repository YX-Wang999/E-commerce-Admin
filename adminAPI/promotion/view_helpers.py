"""Shared view helpers for promotion activities."""

import logging
from datetime import datetime, time

from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from common.response import error_response, success_response

logger = logging.getLogger(__name__)


def filter_activity_queryset(queryset, request: Request, time_field: str = 'start_time'):
    """Apply common list filters."""
    status_param = request.query_params.get('status')
    keyword = request.query_params.get('keyword')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')

    if status_param:
        queryset = queryset.filter(status=status_param)
    if keyword:
        queryset = queryset.filter(name__icontains=keyword)
    if start_date:
        parsed_start = parse_date(start_date)
        if parsed_start:
            start_dt = timezone.make_aware(datetime.combine(parsed_start, time.min))
            queryset = queryset.filter(**{f'{time_field}__gte': start_dt})
    if end_date:
        parsed_end = parse_date(end_date)
        if parsed_end:
            end_dt = timezone.make_aware(datetime.combine(parsed_end, time.max))
            queryset = queryset.filter(**{f'{time_field}__lte': end_dt})
    return queryset


def serializer_error_message(serializer) -> str:
    """Extract first serializer error message."""
    message = next(iter(serializer.errors.values()))[0]
    if isinstance(message, list):
        return str(message[0])
    return str(message)


def list_response(viewset, request: Request, queryset) -> Response:
    """Return paginated list response."""
    queryset = viewset.filter_queryset(queryset)
    page = viewset.paginate_queryset(queryset)
    if page is not None:
        serializer = viewset.get_serializer(page, many=True)
        return viewset.get_paginated_response(serializer.data)
    serializer = viewset.get_serializer(queryset, many=True)
    return success_response(data=serializer.data)


def create_response(viewset, serializer, user, initial_status: str, error_msg: str = '创建失败') -> Response:
    """Create activity and return response."""
    if not serializer.is_valid():
        return error_response(serializer_error_message(serializer))
    try:
        save_kwargs = {'created_by': user, 'status': initial_status}
        tenant = getattr(viewset.request, 'tenant', None)
        if tenant is not None:
            save_kwargs['tenant'] = tenant
        instance = serializer.save(**save_kwargs)
    except Exception:
        logger.exception(error_msg)
        return error_response(error_msg, code=50000, http_status=500)
    return success_response(
        data=viewset.get_serializer(instance).data,
        message='创建成功',
        http_status=status.HTTP_201_CREATED,
    )


def update_response(viewset, instance, request: Request, editable_statuses: set, **kwargs) -> Response:
    """Update activity and return response."""
    if instance.status not in editable_statuses:
        return error_response('当前状态不可编辑')
    partial = kwargs.pop('partial', False)
    serializer = viewset.get_serializer(instance, data=request.data, partial=partial)
    if not serializer.is_valid():
        return error_response(serializer_error_message(serializer))
    try:
        instance = serializer.save()
    except Exception:
        return error_response('更新失败', code=50000, http_status=500)
    return success_response(data=viewset.get_serializer(instance).data, message='更新成功')
