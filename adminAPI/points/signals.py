"""Points-related signal handlers."""

import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from orders.models import Order
from points.services import award_order_points

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Order)
def cache_order_status(sender, instance: Order, **kwargs) -> None:
    """Cache previous status before save."""
    if instance.pk:
        instance._previous_status = (
            Order.objects.filter(pk=instance.pk).values_list('status', flat=True).first()
        )
    else:
        instance._previous_status = None


@receiver(post_save, sender=Order)
def on_order_completed(sender, instance: Order, created: bool, **kwargs) -> None:
    """Award points when order becomes completed."""
    previous = getattr(instance, '_previous_status', None)
    if instance.status == Order.STATUS_COMPLETED and previous != Order.STATUS_COMPLETED:
        try:
            award_order_points(instance)
        except Exception:
            logger.exception('Award order points failed for order %s', instance.id)
        try:
            from membership.services import award_order_growth

            award_order_growth(instance)
        except Exception:
            logger.exception('Award order growth failed for order %s', instance.id)
