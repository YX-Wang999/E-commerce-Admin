"""Logistics tracking services."""

from __future__ import annotations

import hashlib
import json
import logging

import requests
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from logistics.express_companies import get_company_name, normalize_express_code, validate_tracking_number
from logistics.factory import get_logistics_service
from logistics.mock_service import MockLogisticsService
from logistics.mock_traces import ensure_mock_traces
from logistics.models import Logistics

logger = logging.getLogger(__name__)

KUAIDI100_STATE_MAP = {
    '0': Logistics.STATUS_TRANSPORTING,
    '1': Logistics.STATUS_PICKED,
    '2': Logistics.STATUS_EXCEPTION,
    '3': Logistics.STATUS_DELIVERED,
    '4': Logistics.STATUS_DELIVERING,
    '5': Logistics.STATUS_RETURNED,
    '6': Logistics.STATUS_DELIVERING,
}


class Kuaidi100Service:
    """Kuaidi100 poll query API."""

    BASE_URL = 'https://poll.kuaidi100.com/poll/query.do'

    def __init__(self, customer: str | None = None, key: str | None = None):
        self.customer = customer or getattr(settings, 'KUAIDI100_CUSTOMER', '')
        self.key = key or getattr(settings, 'KUAIDI100_KEY', '')

    @property
    def enabled(self) -> bool:
        return bool(self.customer and self.key)

    def query_tracking(self, express_code: str, tracking_number: str) -> dict:
        if not self.enabled:
            return {'status': '503', 'message': '未配置快递100，请在 .env 中设置 KUAIDI100_CUSTOMER 与 KUAIDI100_KEY'}

        param = {'com': express_code, 'num': tracking_number}
        param_str = json.dumps(param, ensure_ascii=False, separators=(',', ':'))
        sign = hashlib.md5(f'{param_str}{self.key}{self.customer}'.encode()).hexdigest().upper()

        try:
            response = requests.post(
                self.BASE_URL,
                data={'customer': self.customer, 'param': param_str, 'sign': sign},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.exception('Kuaidi100 query failed')
            return {'status': '500', 'message': f'物流查询失败: {exc}'}

    def parse_response(self, data: dict) -> dict:
        if str(data.get('status')) != '200':
            return {'error': data.get('message', '查询失败'), 'raw': data}

        traces = []
        for item in data.get('data') or []:
            traces.append({
                'time': item.get('ftime') or item.get('time'),
                'content': item.get('context', ''),
                'status': item.get('status'),
                'area': item.get('areaName') or item.get('areaCode') or '',
            })

        state = str(data.get('state', '0'))
        return {
            'status': KUAIDI100_STATE_MAP.get(state, Logistics.STATUS_TRANSPORTING),
            'traces': traces,
            'last_update': data.get('updatetime') or data.get('updateTime'),
            'raw': data,
        }


def map_kuaidi100_state(state: str | int | None) -> str:
    return KUAIDI100_STATE_MAP.get(str(state or '0'), Logistics.STATUS_TRANSPORTING)


def _parse_trace_time(value: str | None):
    if not value:
        return None
    parsed = parse_datetime(value.replace(' ', 'T', 1) if ' ' in value and 'T' not in value else value)
    if parsed and timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def apply_tracking_result(logistics: Logistics, result: dict) -> Logistics:
    """Apply parsed tracking result onto a Logistics instance."""
    if result.get('error'):
        logistics.raw_response = result.get('raw') or {'error': result['error']}
        logistics.save(update_fields=['raw_response', 'updated_at'])
        return logistics

    traces = result.get('traces') or []
    logistics.traces = traces
    logistics.status = result.get('status') or logistics.status
    logistics.raw_response = result.get('raw') or {}

    if traces:
        latest_time = _parse_trace_time(traces[0].get('time'))
        if latest_time:
            logistics.last_trace_at = latest_time

    for trace in reversed(traces):
        content = trace.get('content') or ''
        trace_time = _parse_trace_time(trace.get('time'))
        if '签收' in content and trace_time:
            logistics.delivered_at = trace_time
            break

    for trace in traces:
        content = trace.get('content') or ''
        trace_time = _parse_trace_time(trace.get('time'))
        if trace_time and any(keyword in content for keyword in ('揽收', '已收寄', '收件')):
            logistics.picked_at = trace_time
            break

    if logistics.status == Logistics.STATUS_DELIVERED and not logistics.delivered_at and logistics.last_trace_at:
        logistics.delivered_at = logistics.last_trace_at

    logistics.save()
    return logistics


def sync_logistics_tracking(logistics: Logistics, *, force: bool = False, advance: bool = False) -> Logistics:
    """Fetch latest tracking and persist."""
    service = get_logistics_service()

    if isinstance(service, MockLogisticsService):
        logistics = ensure_mock_traces(logistics)
        if advance:
            result = service.advance_one_stage(logistics)
            return apply_tracking_result(logistics, result)
        return logistics

    if not force and logistics.last_trace_at:
        age = timezone.now() - logistics.last_trace_at
        if age.total_seconds() < 7200 and logistics.traces:
            return logistics

    raw = service.query_tracking(logistics.express_code, logistics.tracking_number)
    parsed = service.parse_response(raw)
    return apply_tracking_result(logistics, parsed)


def create_or_update_logistics_for_ship(
    *,
    order,
    express_code: str,
    tracking_number: str,
    express_company: str = '',
) -> Logistics:
    """Create logistics record when order ships."""
    error = validate_tracking_number(tracking_number)
    if error:
        raise ValueError(error)

    company = express_company or get_company_name(express_code)
    normalized_code = normalize_express_code(express_code)
    logistics, _created = Logistics.objects.update_or_create(
        order=order,
        defaults={
            'express_company': company,
            'express_code': normalized_code,
            'tracking_number': tracking_number.strip(),
            'status': Logistics.STATUS_PICKED,
        },
    )
    order.logistics_no = logistics.tracking_number
    order.save(update_fields=['logistics_no', 'updated_at'])

    service = get_logistics_service()
    try:
        if isinstance(service, MockLogisticsService):
            result = service.build_initial_trace(logistics)
            apply_tracking_result(logistics, result)
        else:
            sync_logistics_tracking(logistics, force=True)
    except Exception:
        logger.exception('Initial logistics sync failed for order %s', order.id)
    return logistics
