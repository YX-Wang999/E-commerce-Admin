"""Review signal handlers."""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from points.services import award_review_points
from reviews.models import ProductReview

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ProductReview)
def on_review_created(sender, instance: ProductReview, created: bool, **kwargs) -> None:
    """Award points when review created."""
    if not created:
        return
    try:
        award_review_points(instance)
    except Exception:
        logger.exception('Award review points failed for review %s', instance.id)
    try:
        from membership.services import add_growth_points
        from membership.models import GrowthLog

        add_growth_points(
            instance.customer,
            10,
            GrowthLog.TYPE_REVIEW,
            description='商品评价奖励',
            source=f'review_growth:{instance.id}',
        )
    except Exception:
        logger.exception('Award review growth failed for review %s', instance.id)
