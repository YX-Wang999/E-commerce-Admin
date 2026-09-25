"""Auto-confirm receipt for shipped orders after 15 days."""

from django.core.management.base import BaseCommand

from orders.receipt import run_auto_confirm_receipts


class Command(BaseCommand):
    help = 'Auto confirm receipt for shipped orders older than 15 days'

    def handle(self, *args, **options):
        count = run_auto_confirm_receipts()
        self.stdout.write(self.style.SUCCESS(f'Auto confirmed receipt: {count} orders'))
