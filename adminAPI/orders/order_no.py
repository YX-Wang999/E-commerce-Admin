"""Order number generator."""

import random
import uuid

from django.utils import timezone

from orders.models import Order


def generate_order_no() -> str:
    """Generate unique order number: ORD + date + 4 random digits."""
    date_part = timezone.localtime().strftime('%Y%m%d')
    for _ in range(20):
        candidate = f'ORD{date_part}{random.randint(1000, 9999)}'
        if not Order.objects.filter(order_no=candidate).exists():
            return candidate
    return f'ORD{date_part}{uuid.uuid4().hex[:4].upper()}'
