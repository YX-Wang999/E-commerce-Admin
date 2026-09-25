"""Logistics provider factory."""

from django.conf import settings

from logistics.mock_service import MockLogisticsService


class CainiaoService:
    """Cainiao logistics stub — not implemented yet."""

    def sync_tracking(self, logistics, *, force: bool = False):
        raise NotImplementedError('菜鸟物流尚未对接，请将 LOGISTICS_PROVIDER 设为 mock 或 kuaidi100')

    def query_tracking(self, express_code: str, tracking_number: str) -> dict:
        return {'status': '501', 'message': '菜鸟物流尚未对接'}


def get_logistics_service():
    """Return logistics service based on LOGISTICS_PROVIDER setting."""
    provider = getattr(settings, 'LOGISTICS_PROVIDER', 'mock').lower()

    if provider == 'kuaidi100':
        from logistics.services import Kuaidi100Service

        return Kuaidi100Service(
            customer=getattr(settings, 'KUAIDI100_CUSTOMER', ''),
            key=getattr(settings, 'KUAIDI100_KEY', ''),
        )
    if provider == 'cainiao':
        return CainiaoService()

    step_hours = getattr(settings, 'MOCK_LOGISTICS_STEP_HOURS', 6)
    return MockLogisticsService(step_hours=step_hours)


def is_mock_provider() -> bool:
    return getattr(settings, 'LOGISTICS_PROVIDER', 'mock').lower() == 'mock'
