"""Order business logic."""

from __future__ import annotations

import logging
from datetime import timedelta

from django.utils import timezone

from orders.cancellation import cancel_timeout_order, release_failed_group_orders
from orders.models import Order
from tenants.models import Tenant

logger = logging.getLogger(__name__)

ORDER_PENDING_MINUTES = 15


def get_order_expires_at(*, from_time=None):
    """Return expiry datetime for a new pending order."""
    base = from_time or timezone.now()
    return base + timedelta(minutes=ORDER_PENDING_MINUTES)


def is_order_expired(order: Order) -> bool:
    """Check whether a pending order has passed its payment deadline."""
    if order.status != Order.STATUS_PENDING:
        return False
    if not order.expires_at:
        return False
    return order.expires_at <= timezone.now()


def release_expired_order(order: Order) -> bool:
    """Cancel an expired pending order and restore inventory."""
    return cancel_timeout_order(order)


def release_expired_orders() -> int:
    """Release all expired pending orders. Returns count released."""
    expired_ids = list(
        Order.objects.filter(
            status=Order.STATUS_PENDING,
            expires_at__isnull=False,
            expires_at__lte=timezone.now(),
        ).values_list('id', flat=True),
    )
    released = 0
    for order_id in expired_ids:
        try:
            order = Order.objects.get(pk=order_id)
            if release_expired_order(order):
                released += 1
        except Exception:
            logger.exception('Release expired order failed: id=%s', order_id)
    return released


def run_auto_cancellations() -> dict[str, int]:
    """Run timeout and group-buy failure cancellations."""
    return {
        'timeout_orders': release_expired_orders(),
        'groupbuy_orders': release_failed_group_orders(),
    }


def resolve_checkout_tenant(*, products, request, customer):
    """Derive merchant tenant from checkout line products."""
    tenant_ids = {product.tenant_id for product in products if product.tenant_id}
    if len(tenant_ids) > 1:
        return None, '不同店铺的商品请分开下单'
    if len(tenant_ids) == 1:
        tenant_id = tenant_ids.pop()
        tenant = Tenant.objects.filter(
            pk=tenant_id,
            is_active=True,
            status=Tenant.STATUS_ACTIVE,
        ).first()
        if tenant is None:
            return None, '店铺不可用，请稍后再试'
        return tenant, None

    fallback = getattr(request, 'tenant', None) or getattr(customer, 'tenant', None)
    return fallback, None
