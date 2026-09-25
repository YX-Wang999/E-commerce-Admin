"""Check low stock after product save."""

from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from notification.services import LOW_STOCK_THRESHOLD, notify_low_stock
from products.models import Product

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Product)
def notify_product_low_stock(sender, instance: Product, created: bool, **kwargs) -> None:
    if created:
        return
    old_stock = getattr(instance, '_old_stock', None)
    if old_stock is None:
        return
    if old_stock > LOW_STOCK_THRESHOLD >= instance.stock:
        try:
            notify_low_stock(product=instance)
        except Exception:
            logger.exception('Low stock notification failed for product %s', instance.pk)
