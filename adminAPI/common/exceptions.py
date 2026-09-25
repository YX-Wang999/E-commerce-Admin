"""Custom exception handler for DRF."""

import logging
from typing import Any, Optional

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

from common.codes import LOGIN_REQUIRED
from customers.exceptions import CustomerLoginRequired

logger = logging.getLogger(__name__)


def custom_exception_handler(
    exc: Exception,
    context: dict[str, Any],
) -> Optional[Response]:
    """Convert DRF exceptions to unified response format."""
    if isinstance(exc, CustomerLoginRequired):
        detail = exc.detail
        message = str(detail) if not isinstance(detail, list) else str(detail[0])
        return Response(
            {'code': LOGIN_REQUIRED, 'data': None, 'message': message},
            status=exc.status_code,
        )

    response = exception_handler(exc, context)
    if response is None:
        logger.exception('Unhandled exception: %s', exc)
        return Response(
            {
                'code': 50000,
                'data': None,
                'message': '服务器内部错误',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    message = '请求失败'
    if isinstance(response.data, dict):
        if 'detail' in response.data:
            message = str(response.data['detail'])
        else:
            first_key = next(iter(response.data))
            first_value = response.data[first_key]
            if isinstance(first_value, list) and first_value:
                message = str(first_value[0])
            else:
                message = str(first_value)
    elif isinstance(response.data, list) and response.data:
        message = str(response.data[0])

    code_map = {
        status.HTTP_401_UNAUTHORIZED: 40100,
        status.HTTP_403_FORBIDDEN: 40300,
        status.HTTP_404_NOT_FOUND: 40400,
    }
    code = code_map.get(response.status_code, 40001)

    return Response(
        {'code': code, 'data': None, 'message': message},
        status=response.status_code,
    )
