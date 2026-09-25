"""Release expired pending orders and restore inventory."""

from django.core.management.base import BaseCommand

from orders.services import release_expired_orders


class Command(BaseCommand):
    help = 'Cancel pending orders past expires_at and restore product stock'

    def handle(self, *args, **options):
        count = release_expired_orders()
        self.stdout.write(self.style.SUCCESS(f'Released {count} expired order(s)'))
