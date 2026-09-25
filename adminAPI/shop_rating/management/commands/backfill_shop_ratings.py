"""Backfill shop ratings from existing tenants and reviews."""

from django.core.management.base import BaseCommand

from reviews.models import ProductReview
from shop_rating.services import ensure_shop_rating, sync_user_rating_from_product_review, update_shop_score
from tenants.models import Tenant


class Command(BaseCommand):
    help = 'Initialize shop ratings for all tenants and sync from product reviews'

    def handle(self, *args, **options):
        tenant_count = 0
        for tenant in Tenant.objects.all().iterator():
            ensure_shop_rating(tenant)
            tenant_count += 1

        review_count = 0
        for review in ProductReview.objects.select_related('product').iterator():
            sync_user_rating_from_product_review(review)
            review_count += 1

        for tenant in Tenant.objects.all().iterator():
            update_shop_score(tenant)

        self.stdout.write(
            self.style.SUCCESS(
                f'Initialized {tenant_count} tenants and synced {review_count} reviews',
            ),
        )
