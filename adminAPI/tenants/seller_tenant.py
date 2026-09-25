"""Resolve seller tenant from header or staff membership."""

from tenants.context import set_current_tenant
from tenants.models import Tenant


def resolve_seller_tenant(request) -> Tenant | None:
    tenant = getattr(request, 'tenant', None)
    if tenant is None:
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return None
        staff = (
            user.tenant_staffs.filter(
                is_active=True,
                tenant__status__in=[Tenant.STATUS_ACTIVE, Tenant.STATUS_SUSPENDED],
            )
            .select_related('tenant')
            .order_by('-id')
            .first()
        )
        if staff is None:
            return None
        tenant = staff.tenant
        request.tenant = tenant
    set_current_tenant(tenant)
    return tenant
