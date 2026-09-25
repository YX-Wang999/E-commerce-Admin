"""Unified API response helpers."""

from typing import Any, Optional

from rest_framework.response import Response
from rest_framework import status


def success_response(
    data: Any = None,
    message: str = 'success',
    code: int = 0,
    http_status: int = status.HTTP_200_OK,
) -> Response:
    """Return a successful API response."""
    return Response(
        {'code': code, 'data': data, 'message': message},
        status=http_status,
    )


def error_response(
    message: str,
    code: int = 40001,
    data: Any = None,
    http_status: int = status.HTTP_400_BAD_REQUEST,
) -> Response:
    """Return an error API response."""
    return Response(
        {'code': code, 'data': data, 'message': message},
        status=http_status,
    )


def status_blocked_response(
    message: str,
    *,
    data: Any = None,
    code: int = 403,
) -> Response:
    """Return a blocked-status response for login or access checks."""
    return Response(
        {'code': code, 'data': data, 'message': message},
        status=status.HTTP_403_FORBIDDEN,
    )
