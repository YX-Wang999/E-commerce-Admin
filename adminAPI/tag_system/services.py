"""Tag resolution and display helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from django.db.models import Prefetch, Q
from django.utils import timezone

from tag_system.models import ProductTagConfig, Tag, TagCategory, TenantTagConfig

TYPE_PRIORITY = {
    TagCategory.CATEGORY_PLATFORM: 300,
    TagCategory.CATEGORY_TENANT: 200,
    TagCategory.CATEGORY_PRODUCT: 100,
}

DEFAULT_TAGS: list[dict[str, Any]] = [
    {
        'name': '国补',
        'code': 'subsidy',
        'category_type': TagCategory.CATEGORY_PLATFORM,
        'color': '#FF6B35',
        'requires_approval': True,
        'priority': 90,
    },
    {
        'name': '百亿补贴',
        'code': 'billion_subsidy',
        'category_type': TagCategory.CATEGORY_PLATFORM,
        'color': '#FF4757',
        'requires_approval': True,
        'priority': 85,
    },
    {
        'name': '超级立减',
        'code': 'super_discount',
        'category_type': TagCategory.CATEGORY_PLATFORM,
        'color': '#2ED573',
        'requires_approval': True,
        'priority': 80,
    },
    {
        'name': '秒杀',
        'code': 'seckill',
        'category_type': TagCategory.CATEGORY_PRODUCT,
        'color': '#FF4757',
        'priority': 75,
    },
    {
        'name': '团购',
        'code': 'groupbuy',
        'category_type': TagCategory.CATEGORY_PRODUCT,
        'color': '#FF6B81',
        'priority': 70,
    },
    {
        'name': '积分可用',
        'code': 'points_available',
        'category_type': TagCategory.CATEGORY_PRODUCT,
        'color': '#1E90FF',
        'icon': '⭐',
        'priority': 65,
    },
    {
        'name': '店铺满减',
        'code': 'store_discount',
        'category_type': TagCategory.CATEGORY_TENANT,
        'color': '#FFA502',
        'priority': 60,
    },
    {
        'name': '新品',
        'code': 'new_arrival',
        'category_type': TagCategory.CATEGORY_PRODUCT,
        'color': '#5352ED',
        'priority': 55,
    },
]


def seed_default_tags() -> None:
    """Create default tag categories and tags."""
    categories: dict[str, TagCategory] = {}
    for cat_type, label in TagCategory.CATEGORY_TYPES:
        category, _ = TagCategory.objects.update_or_create(
            code=cat_type,
            defaults={
                'name': label,
                'category_type': cat_type,
                'sort_order': {'platform': 1, 'tenant': 2, 'product': 3}.get(cat_type, 99),
                'is_active': True,
            },
        )
        categories[cat_type] = category

    for item in DEFAULT_TAGS:
        category = categories[item['category_type']]
        Tag.objects.update_or_create(
            code=item['code'],
            defaults={
                'name': item['name'],
                'category': category,
                'color': item.get('color', '#FF6B35'),
                'text_color': item.get('text_color', '#FFFFFF'),
                'icon': item.get('icon', ''),
                'priority': item.get('priority', 50),
                'requires_approval': item.get('requires_approval', False),
                'is_active': True,
                'can_tenant_use': True,
                'can_product_use': True,
            },
        )


def _now() -> datetime:
    return timezone.now()


def _in_time_window(start_time, end_time, now: datetime) -> bool:
    if start_time and start_time > now:
        return False
    if end_time and end_time < now:
        return False
    return True


def _serialize_tag(tag: Tag, display_text: str = '') -> dict[str, Any]:
    return {
        'code': tag.code,
        'name': display_text or tag.name,
        'color': tag.color,
        'text_color': tag.text_color,
        'icon': tag.icon or '',
        'category_type': tag.category.category_type,
        'priority': tag.priority + TYPE_PRIORITY.get(tag.category.category_type, 0),
    }


def _tenant_can_use_tag(tenant_id: int | None, tag: Tag, tenant_config_map: dict) -> bool:
    if tag.category.category_type != TagCategory.CATEGORY_PLATFORM:
        return True
    if not tenant_id:
        return True
    if not tag.requires_approval:
        return True
    cfg = tenant_config_map.get((tenant_id, tag.id))
    if not cfg:
        return False
    return (
        cfg.is_participating
        and cfg.status == TenantTagConfig.STATUS_APPROVED
        and _in_time_window(cfg.start_time, cfg.end_time, _now())
    )


def _collect_manual_tags(product, tenant_config_map: dict) -> list[dict[str, Any]]:
    tags: list[dict[str, Any]] = []
    now = _now()
    prefetched = getattr(product, '_prefetched_tag_configs', None)
    if prefetched is None:
        configs = (
            ProductTagConfig.objects.filter(product_id=product.id, is_active=True)
            .select_related('tag', 'tag__category')
        )
    else:
        configs = [row for row in prefetched if row.is_active]

    for cfg in configs:
        if not _in_time_window(cfg.start_time, cfg.end_time, now):
            continue
        tag = cfg.tag
        if not tag.is_active:
            continue
        if cfg.source_type != ProductTagConfig.SOURCE_PLATFORM and not _tenant_can_use_tag(
            product.tenant_id,
            tag,
            tenant_config_map,
        ):
            continue
        tags.append(_serialize_tag(tag, cfg.display_text))
    return tags


def _collect_auto_tags(product, tenant_config_map: dict) -> list[dict[str, Any]]:
    """Infer tags from existing promo modules when no manual config exists."""
    from promotion.models import SeckillActivity
    from seller_points.models import SellerPointsRule
    from subsidy.models import SubsidyProduct

    tags: list[dict[str, Any]] = []
    tag_by_code = {tag.code: tag for tag in Tag.objects.filter(is_active=True).select_related('category')}
    now = _now()
    manual_codes = {
        cfg.tag.code
        for cfg in getattr(product, '_prefetched_tag_configs', []) or []
        if cfg.is_active
    }

    if 'subsidy' not in manual_codes:
        subsidy_tag = tag_by_code.get('subsidy')
        if subsidy_tag and SubsidyProduct.objects.filter(
            product_id=product.id,
            filing_status=SubsidyProduct.FILING_APPROVED,
        ).exists():
            if _tenant_can_use_tag(product.tenant_id, subsidy_tag, tenant_config_map):
                tags.append(_serialize_tag(subsidy_tag))

    if 'seckill' not in manual_codes:
        seckill_tag = tag_by_code.get('seckill')
        if seckill_tag and SeckillActivity.objects.filter(
            products=product.id,
            status=SeckillActivity.STATUS_RUNNING,
            start_time__lte=now,
            end_time__gte=now,
        ).exists():
            tags.append(_serialize_tag(seckill_tag))

    if product.tenant_id and 'points_available' not in manual_codes:
        points_tag = tag_by_code.get('points_available')
        if points_tag and SellerPointsRule.objects.filter(
            tenant_id=product.tenant_id,
            is_active=True,
        ).exists():
            tags.append(_serialize_tag(points_tag))

    return tags


def get_display_tags_for_product(product, limit: int = 3) -> list[dict[str, Any]]:
    tenant_config_map: dict = getattr(product, '_tenant_tag_config_map', {})
    manual = _collect_manual_tags(product, tenant_config_map)
    manual_codes = {item['code'] for item in manual}
    auto = [item for item in _collect_auto_tags(product, tenant_config_map) if item['code'] not in manual_codes]
    combined = manual + auto
    combined.sort(key=lambda item: item['priority'], reverse=True)
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in combined:
        if item['code'] in seen:
            continue
        seen.add(item['code'])
        deduped.append({
            'code': item['code'],
            'name': item['name'],
            'color': item['color'],
            'text_color': item['text_color'],
            'icon': item['icon'],
        })
        if len(deduped) >= limit:
            break
    return deduped


def attach_product_tags(products: list) -> None:
    """Prefetch tag configs for a product list queryset/items."""
    if not products:
        return
    product_ids = [p.id for p in products]
    tenant_ids = {p.tenant_id for p in products if p.tenant_id}

    configs = (
        ProductTagConfig.objects.filter(product_id__in=product_ids, is_active=True)
        .select_related('tag', 'tag__category')
    )
    config_map: dict[int, list] = {}
    for cfg in configs:
        config_map.setdefault(cfg.product_id, []).append(cfg)

    tenant_configs = TenantTagConfig.objects.filter(tenant_id__in=tenant_ids).select_related('tag')
    tenant_map = {(cfg.tenant_id, cfg.tag_id): cfg for cfg in tenant_configs}

    for product in products:
        product._prefetched_tag_configs = config_map.get(product.id, [])
        product._tenant_tag_config_map = {
            key: value
            for key, value in tenant_map.items()
            if key[0] == product.tenant_id
        }
