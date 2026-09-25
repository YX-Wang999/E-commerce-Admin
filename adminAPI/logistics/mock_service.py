"""Mock logistics service for development and demo."""

from __future__ import annotations

from django.utils import timezone

from logistics.mock_traces import (
    _STAGE_BLUEPRINT,
    _STATUS_INDEX,
    advance_mock_stage,
    mock_result_for_order,
)
from logistics.models import Logistics


class MockLogisticsService:
    """Simulated logistics tracking for dev/demo environments."""

    def __init__(self, step_hours: float = 6):
        self.step_hours = max(float(step_hours or 6), 0.5)

    def build_initial_trace(self, logistics: Logistics) -> dict:
        """First node only: picked at origin hub."""
        return mock_result_for_order(logistics.order, max_stage_index=0)

    def advance_one_stage(self, logistics: Logistics) -> dict:
        """Advance by one stage when admin clicks refresh."""
        return advance_mock_stage(logistics)

    def _target_stage_index(self, logistics: Logistics, *, force: bool = False) -> int:
        base_time = logistics.picked_at or logistics.created_at
        if not base_time:
            return 0

        elapsed_hours = (timezone.now() - base_time).total_seconds() / 3600
        time_based = min(len(_STAGE_BLUEPRINT) - 1, int(elapsed_hours // self.step_hours))

        current_index = _STATUS_INDEX.get(logistics.status, 0)
        if force:
            return max(current_index, time_based)
        return max(current_index, min(time_based, current_index + 1))

    def advance_if_due(self, logistics: Logistics, *, force: bool = False) -> dict:
        """Time-based advance for scheduled jobs."""
        target_index = self._target_stage_index(logistics, force=force)
        return mock_result_for_order(logistics.order, max_stage_index=target_index)

    def query_tracking(self, express_code: str, tracking_number: str) -> dict:
        return {'status': '200', 'state': '3', 'data': []}

    def parse_response(self, data: dict) -> dict:
        traces = []
        for item in data.get('data') or []:
            traces.append({
                'time': item.get('ftime') or item.get('time'),
                'content': item.get('context', ''),
                'status': Logistics.STATUS_DELIVERED,
                'area': '',
            })
        return {
            'status': Logistics.STATUS_DELIVERED,
            'traces': traces,
            'raw': data,
        }
