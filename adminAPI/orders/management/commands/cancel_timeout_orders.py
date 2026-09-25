"""Auto-cancel timeout and failed group-buy orders."""

from django.core.management.base import BaseCommand

from orders.services import run_auto_cancellations


class Command(BaseCommand):
    help = 'Cancel pending orders past expires_at (15 min) and failed group-buy orders'

    def handle(self, *args, **options):
        stats = run_auto_cancellations()
        self.stdout.write(
            self.style.SUCCESS(
                f"Cancelled timeout orders: {stats['timeout_orders']}, "
                f"group-buy failed: {stats['groupbuy_orders']}",
            ),
        )
