"""Sync in-transit logistics (mock advance or Kuaidi100 poll)."""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from logistics.factory import is_mock_provider
from logistics.models import Logistics
from logistics.services import sync_logistics_tracking


class Command(BaseCommand):
    help = 'Update logistics: mock mode advances simulated stages; kuaidi100 polls API'

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=7)
        active_statuses = [
            Logistics.STATUS_PICKED,
            Logistics.STATUS_TRANSPORTING,
            Logistics.STATUS_DELIVERING,
        ]
        queryset = Logistics.objects.filter(
            status__in=active_statuses,
            updated_at__gte=cutoff,
        ).select_related('order')

        updated = 0
        failed = 0
        provider = 'mock' if is_mock_provider() else 'kuaidi100'
        self.stdout.write(f'Provider: {provider}, records: {queryset.count()}')

        for logistics in queryset:
            try:
                before = logistics.status
                sync_logistics_tracking(logistics, force=True)
                logistics.refresh_from_db()
                updated += 1
                if logistics.status != before:
                    self.stdout.write(
                        f'Order {logistics.order_id}: {before} -> {logistics.status}',
                    )
            except Exception as exc:
                failed += 1
                self.stderr.write(f'Order {logistics.order_id}: {exc}')

        self.stdout.write(self.style.SUCCESS(f'Updated {updated} records, {failed} failed'))
