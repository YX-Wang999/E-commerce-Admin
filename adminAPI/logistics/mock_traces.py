"""Mock logistics trace generation for demo / dev."""

from __future__ import annotations

import re
from datetime import timedelta

from django.utils import timezone

from logistics.models import Logistics

_CITY_PATTERN = re.compile(r'([\u4e00-\u9fff]{2,10}?市)')

_STAGE_BLUEPRINT = [
    (Logistics.STATUS_PICKED, 'origin', '【{city_full}】已揽收，{city_short}转运中心'),
    (Logistics.STATUS_TRANSPORTING, 'origin', '【{city_full}】运输中，快件已发往{dest_short}'),
    (Logistics.STATUS_DELIVERING, 'dest', '【{city_full}】派送中，快递员：张师傅 138****1234'),
    (Logistics.STATUS_DELIVERED, 'dest', '【{city_full}】已签收，本人签收'),
]

_STATUS_INDEX = {status: index for index, (status, _, _) in enumerate(_STAGE_BLUEPRINT)}

_ORIGIN_HUB = ('广州市', '广州')


def guess_city(address: str) -> tuple[str, str]:
    text = (address or '').strip()
    match = _CITY_PATTERN.search(text)
    city_full = match.group(1) if match else '深圳市'
    city_short = city_full.replace('市', '')
    return city_full, city_short


def resolve_route_cities(order) -> tuple[tuple[str, str], tuple[str, str]]:
    dest_full, dest_short = guess_city(getattr(order, 'address', '') or '')
    origin_full, origin_short = _ORIGIN_HUB
    if origin_full == dest_full:
        origin_full, origin_short = ('深圳市', '深圳')
    return (origin_full, origin_short), (dest_full, dest_short)


def generate_mock_traces(order, *, max_stage_index: int | None = None) -> list[dict]:
    """Build mock traces newest-first, with origin/destination cities for map routes."""
    (origin_full, origin_short), (dest_full, dest_short) = resolve_route_cities(order)
    last_index = len(_STAGE_BLUEPRINT) - 1 if max_stage_index is None else min(max_stage_index, len(_STAGE_BLUEPRINT) - 1)

    now = timezone.now()
    chronological = []
    for index, (status, city_role, template) in enumerate(_STAGE_BLUEPRINT):
        if index > last_index:
            break
        if city_role == 'origin':
            city_full, city_short = origin_full, origin_short
        else:
            city_full, city_short = dest_full, dest_short
        hours_ago = (last_index - index) * 6
        chronological.append({
            'time': (now - timedelta(hours=hours_ago)).strftime('%Y-%m-%d %H:%M:%S'),
            'content': template.format(
                city_full=city_full,
                city_short=city_short,
                dest_short=dest_short,
            ),
            'city': city_short,
            'area': city_full,
            'status': status,
        })

    return list(reversed(chronological))


def get_stage_index(logistics: Logistics) -> int:
    """Current mock stage (0=picked .. 3=delivered)."""
    raw = logistics.raw_response or {}
    if isinstance(raw, dict) and raw.get('provider') == 'mock' and 'stage' in raw:
        return int(raw['stage'])

    traces = list(logistics.traces or [])
    if traces:
        return min(len(traces) - 1, len(_STAGE_BLUEPRINT) - 1)

    return _STATUS_INDEX.get(logistics.status, 0)


def mock_result_for_order(order, *, max_stage_index: int | None = None) -> dict:
    traces = generate_mock_traces(order, max_stage_index=max_stage_index)
    stage_index = get_stage_index_from_traces(traces, max_stage_index)
    status = _STAGE_BLUEPRINT[stage_index][0] if traces else Logistics.STATUS_PICKED
    return {
        'status': status,
        'traces': traces,
        'raw': {'provider': 'mock', 'stage': stage_index},
    }


def get_stage_index_from_traces(traces: list[dict], max_stage_index: int | None) -> int:
    if not traces:
        return 0
    if max_stage_index is not None:
        return min(max_stage_index, len(_STAGE_BLUEPRINT) - 1)
    return min(len(traces) - 1, len(_STAGE_BLUEPRINT) - 1)


def advance_mock_stage(logistics: Logistics) -> dict:
    """Advance mock logistics by one stage (admin manual refresh)."""
    current = get_stage_index(logistics)
    target = min(current + 1, len(_STAGE_BLUEPRINT) - 1)
    return mock_result_for_order(logistics.order, max_stage_index=target)


def enrich_trace_cities(traces: list[dict], order) -> list[dict]:
    (_, _), (dest_full, _) = resolve_route_cities(order)
    enriched = []
    total = len(traces)
    for index, item in enumerate(traces):
        row = dict(item)
        if row.get('city') and row.get('area'):
            enriched.append(row)
            continue
        content = row.get('content') or ''
        match = re.search(r'【([\u4e00-\u9fff]{2,10}?市?)】', content)
        if match:
            name = match.group(1)
            city_full = name if name.endswith('市') else f'{name}市'
        elif row.get('area'):
            area = str(row['area'])
            city_full = area if area.endswith('市') else f'{area}市'
        else:
            city_full = dest_full if index >= total // 2 else _ORIGIN_HUB[0]
        city_short = city_full.replace('市', '')
        row['city'] = row.get('city') or city_short
        row['area'] = row.get('area') or city_full
        enriched.append(row)
    return enriched


def ensure_mock_traces(logistics: Logistics) -> Logistics:
    """Ensure mock traces exist with city fields; never auto-advance stage."""
    from logistics.services import apply_tracking_result

    traces = list(logistics.traces or [])
    if not traces:
        result = mock_result_for_order(logistics.order, max_stage_index=0)
        return apply_tracking_result(logistics, result)

    if not any(item.get('city') for item in traces):
        stage_index = get_stage_index(logistics)
        result = mock_result_for_order(logistics.order, max_stage_index=stage_index)
        return apply_tracking_result(logistics, result)

    enriched = enrich_trace_cities(traces, logistics.order)
    if enriched != traces:
        logistics.traces = enriched
        logistics.save(update_fields=['traces', 'updated_at'])
    return logistics
