"""Process points expiry reminders and auto-deduction."""

from django.core.management.base import BaseCommand

from points.expiry import process_points_expiry


class Command(BaseCommand):
    help = 'Send points expiry reminders (30/7/1 days) and deduct expired balances'

    def handle(self, *args, **options):
        result = process_points_expiry()
        self.stdout.write(
            self.style.SUCCESS(
                'Points expiry processed: '
                f'remind_30={result.get("remind_30", 0)}, '
                f'remind_7={result.get("remind_7", 0)}, '
                f'remind_1={result.get("remind_1", 0)}, '
                f'expired={result.get("expired", 0)}'
            )
        )
