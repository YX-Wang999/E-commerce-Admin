"""Audit middleware."""

import json
import logging
from typing import Callable

from django.http import HttpRequest, HttpResponse

from audit.models import OperationLog

logger = logging.getLogger(__name__)

AUDIT_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}
MODULE_MAP = {
    '/api/users/': '用户管理',
    '/api/roles/': '角色管理',
    '/api/menus/': '菜单管理',
    '/api/permissions/': '权限管理',
    '/api/audit/logs/': '操作日志',
    '/api/system/settings/': '系统设置',
    '/api/departments/': '部门管理',
    '/api/org/': '组织架构',
    '/api/products/': '商品管理',
    '/api/orders/': '订单管理',
    '/api/customers/': '客户管理',
    '/api/feedback/': '客户留言',
    '/api/announcements/': '系统公告',
    '/api/points/': '积分管理',
    '/api/reviews/': '商品评价',
    '/api/reports/': '数据报表',
    '/api/upload/': '文件上传',
}
ACTION_MAP = {
    'POST': OperationLog.ACTION_CREATE,
    'PUT': OperationLog.ACTION_UPDATE,
    'PATCH': OperationLog.ACTION_UPDATE,
    'DELETE': OperationLog.ACTION_DELETE,
}


def _resolve_module(path: str) -> str:
    """Resolve module name from request path."""
    for prefix, module_name in MODULE_MAP.items():
        if path.startswith(prefix):
            return module_name
    return '其他'


def _resolve_action(method: str) -> str:
    """Resolve action from HTTP method."""
    return ACTION_MAP.get(method, OperationLog.ACTION_OTHER)


def _get_client_ip(request: HttpRequest) -> str | None:
    """Extract client IP from request."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class OperationLogMiddleware:
    """Middleware to record mutating API requests."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Initialize middleware."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request and log mutating operations."""
        response = self.get_response(request)
        if (
            request.method in AUDIT_METHODS
            and request.path.startswith('/api/')
            and not request.path.startswith('/api/auth/')
            and response.status_code < 400
        ):
            try:
                user = getattr(request, 'user', None)
                detail = ''
                raw_body = getattr(request, '_body', b'') or b''
                if raw_body:
                    try:
                        body = json.loads(raw_body.decode('utf-8'))
                        detail = json.dumps(body, ensure_ascii=False)[:2000]
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        detail = ''
                OperationLog.objects.create(
                    user=user if user and user.is_authenticated else None,
                    username=user.username if user and user.is_authenticated else '',
                    module=_resolve_module(request.path),
                    action=_resolve_action(request.method),
                    resource=request.path,
                    detail=detail,
                    ip=_get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
                    request_method=request.method,
                    request_path=request.path[:512],
                )
            except Exception:
                logger.exception('Failed to write operation log')
        return response
