"""Common middleware."""

from __future__ import annotations

from tenants.context import clear_current_tenant, set_current_tenant
from tenants.models import Tenant

RESERVED_SUBDOMAINS = frozenset(
    {'www', 'api', 'admin', 'localhost', '127', '0', 'static', 'media'},
)


class TenantMiddleware:
    """Resolve current tenant from X-Tenant-Code header or subdomain."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = self._resolve_tenant(request)
        request.tenant = tenant
        set_current_tenant(tenant)
        try:
            return self.get_response(request)
        finally:
            clear_current_tenant()

    def _resolve_tenant(self, request):
        tenant_code = (request.headers.get('X-Tenant-Code') or '').strip()
        if not tenant_code:
            tenant_code = self._subdomain_from_host(request.get_host())

        if not tenant_code or tenant_code.lower() in RESERVED_SUBDOMAINS:
            return None

        try:
            return Tenant.objects.get(
                code__iexact=tenant_code,
                is_active=True,
                status=Tenant.STATUS_ACTIVE,
            )
        except Tenant.DoesNotExist:
            return None

    @staticmethod
    def _subdomain_from_host(host: str) -> str | None:
        host = (host or '').split(':')[0].strip().lower()
        if not host or host in {'localhost', '127.0.0.1'}:
            return None
        parts = host.split('.')
        if len(parts) < 3:
            return None
        return parts[0]
