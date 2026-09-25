"""Award seller points when orders complete."""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from orders.models import Order
from seller_points.services import award_order_seller_points

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Order)
def on_order_completed_seller_points(sender, instance: Order, created: bool, **kwargs) -> None:
    previous = getattr(instance, '_previous_status', None)
    if instance.status == Order.STATUS_COMPLETED and previous != Order.STATUS_COMPLETED:
        try:
            award_order_seller_points(instance)
        except Exception:
            logger.exception('Award seller points failed for order %s', instance.id)
