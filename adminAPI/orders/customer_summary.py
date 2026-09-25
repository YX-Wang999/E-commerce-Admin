"""Customer order summary counts for mall profile badges."""

from __future__ import annotations

from django.db.models import Count

from chat.models import Complaint
from orders.models import Order


def build_customer_order_summary(customer) -> dict[str, int]:
    base = Order.objects.filter(customer=customer)
    pending = base.filter(status=Order.STATUS_PENDING).count()
    paid = base.filter(
        status=Order.STATUS_PAID,
    ).exclude(cancel_status=Order.CANCEL_STATUS_PENDING).count()
    shipped = base.filter(status=Order.STATUS_SHIPPED).count()
    pending_review = base.filter(status=Order.STATUS_COMPLETED).annotate(
        review_count=Count('reviews'),
    ).filter(review_count=0).count()
    refunding = base.filter(status=Order.STATUS_REFUNDING).count()
    active_complaints = Complaint.objects.filter(
        customer=customer,
    ).exclude(
        status__in=[
            Complaint.STATUS_RESOLVED,
            Complaint.STATUS_REJECTED,
            Complaint.STATUS_CLOSED,
        ],
    ).count()
    return {
        'pending_count': pending,
        'paid_count': paid,
        'shipped_count': shipped,
        'pending_review_count': pending_review,
        'aftersale_count': refunding + active_complaints,
    }
