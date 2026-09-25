"""Shop rating signals."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from reviews.models import ProductReview
from shop_rating.services import ensure_shop_rating, sync_user_rating_from_product_review
from tenants.models import Tenant


@receiver(post_save, sender=Tenant)
def create_shop_rating_for_tenant(sender, instance, created, **kwargs):
    if created:
        ensure_shop_rating(instance)


@receiver(post_save, sender=ProductReview)
def sync_shop_rating_from_review(sender, instance, **kwargs):
    sync_user_rating_from_product_review(instance)
