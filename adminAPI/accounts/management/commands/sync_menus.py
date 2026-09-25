"""Sync platform sidebar menus for deployed environments."""

from django.core.management.base import BaseCommand

from accounts.menu_sync import sync_all_menus


class Command(BaseCommand):
    help = 'Sync platform sidebar menus and default role menu bindings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-roles',
            action='store_true',
            help='Only upsert menus, do not refresh role menu assignments',
        )

    def handle(self, *args, **options):
        stats = sync_all_menus(refresh_roles=not options['skip_roles'])
        self.stdout.write(
            self.style.SUCCESS(
                f"Menus synced: {stats['menu_count']} menus, roles refreshed: {stats['role_count']}",
            ),
        )
