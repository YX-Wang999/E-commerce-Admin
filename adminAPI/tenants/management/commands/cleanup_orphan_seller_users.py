"""Remove seller portal users left behind after tenant deletion."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from tenants.utils import cleanup_orphan_seller_user

User = get_user_model()


class Command(BaseCommand):
    help = 'Delete seller users that no longer belong to any tenant'

    def handle(self, *args, **options):
        deleted = 0
        for user in User.objects.all().iterator():
            username = user.username
            if cleanup_orphan_seller_user(user):
                deleted += 1
                self.stdout.write(f'Deleted orphan seller user: {username}')
        self.stdout.write(self.style.SUCCESS(f'Cleanup complete. Deleted {deleted} user(s).'))
