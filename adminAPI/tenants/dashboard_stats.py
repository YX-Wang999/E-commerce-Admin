"""Shared dashboard statistics helpers."""

from __future__ import annotations

from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone

from chat.models import Complaint
from orders.models import Order


def today_start():
    return timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)


def format_money(value) -> str:
    amount = Decimal(str(value or 0))
    return f'{amount.quantize(Decimal("0.01")):.2f}'


def compute_seller_dashboard_stats(tenant) -> dict:
    paid_statuses = [Order.STATUS_PAID, Order.STATUS_SHIPPED, Order.STATUS_COMPLETED]
    start = today_start()
    order_qs = Order.all_objects.filter(tenant=tenant)

    customer_count = (
        order_qs.exclude(customer_id__isnull=True)
        .aggregate(total=Count('customer_id', distinct=True))['total']
        or 0
    )
    today_orders = order_qs.filter(created_at__gte=start).count()
    paid_orders = order_qs.filter(status=Order.STATUS_PAID).count()
    cancelled_orders = order_qs.filter(status=Order.STATUS_CANCELLED).count()
    today_sales = (
        order_qs.filter(created_at__gte=start, status__in=paid_statuses)
        .aggregate(total=Sum('total_amount'))['total']
        or 0
    )
    total_revenue = (
        order_qs.filter(status__in=paid_statuses).aggregate(total=Sum('total_amount'))['total'] or 0
    )

    return {
        'order_count': order_qs.count(),
        'customer_count': customer_count,
        'today_orders': today_orders,
        'paid_orders': paid_orders,
        'cancelled_orders': cancelled_orders,
        'today_sales': format_money(today_sales),
        'total_revenue': format_money(total_revenue),
    }


def compute_tenant_stats(tenant) -> dict:
    from chat.models import Conversation
    from products.models import Product

    order_stats = compute_seller_dashboard_stats(tenant)
    return {
        'product_count': Product.all_objects.filter(tenant=tenant, is_active=True).count(),
        'order_count': order_stats['order_count'],
        'customer_count': order_stats['customer_count'],
        'conversation_count': Conversation.all_objects.filter(tenant=tenant).count(),
        'paid_orders': order_stats['paid_orders'],
        'cancelled_orders': order_stats['cancelled_orders'],
        'total_revenue': order_stats['total_revenue'],
    }
