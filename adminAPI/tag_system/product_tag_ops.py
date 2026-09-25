"""Product tag batch sync helpers."""

from __future__ import annotations

import logging
import re

from django.db import DatabaseError, transaction

from products.models import Product
from tag_system.models import ProductTagConfig, Tag, TagCategory, TenantTagConfig

logger = logging.getLogger(__name__)

MAX_ACTIVE_PRODUCT_TAGS = 3
_MISSING_TABLE_RE = re.compile(r'no such table|does not exist|doesn\'t exist', re.I)


class ProductTagSyncError(ValueError):
    """Business validation error for product tag sync."""


def _is_missing_table_error(exc: DatabaseError) -> bool:
    return bool(_MISSING_TABLE_RE.search(str(exc)))


def _validate_platform_tag(tenant_id: int | None, tag: Tag) -> None:
    category = getattr(tag, 'category', None)
    if not category or category.category_type != TagCategory.CATEGORY_PLATFORM:
        return
    if not tag.requires_approval:
        return
    if not tenant_id:
        return
    cfg = TenantTagConfig.objects.filter(
        tenant_id=tenant_id,
        tag=tag,
        is_participating=True,
        status=TenantTagConfig.STATUS_APPROVED,
    ).first()
    if not cfg:
        raise ProductTagSyncError('请先申请并等待平台审核通过该标签活动')


@transaction.atomic
def sync_product_tags(
    *,
    product: Product,
    active_tag_ids: list[int],
    source_type: str,
    validate_platform_approval: bool = True,
) -> list[ProductTagConfig]:
    """Activate up to MAX_ACTIVE_PRODUCT_TAGS tags for a product in one transaction."""
    deduped_ids: list[int] = []
    seen: set[int] = set()
    for tag_id in active_tag_ids:
        try:
            normalized = int(tag_id)
        except (TypeError, ValueError):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped_ids.append(normalized)

    if len(deduped_ids) > MAX_ACTIVE_PRODUCT_TAGS:
        raise ProductTagSyncError(f'最多选择 {MAX_ACTIVE_PRODUCT_TAGS} 个促销标签')

    tags = list(
        Tag.objects.filter(pk__in=deduped_ids, is_active=True).select_related('category'),
    )
    tag_map = {tag.id: tag for tag in tags}
    missing = [tag_id for tag_id in deduped_ids if tag_id not in tag_map]
    if missing:
        raise ProductTagSyncError('存在无效或已停用的标签')

    if validate_platform_approval:
        for tag_id in deduped_ids:
            _validate_platform_tag(product.tenant_id, tag_map[tag_id])

    active_id_set = set(deduped_ids)
    ProductTagConfig.objects.filter(product=product).exclude(tag_id__in=active_id_set).update(
        is_active=False,
    )

    rows: list[ProductTagConfig] = []
    for tag_id in deduped_ids:
        tag = tag_map[tag_id]
        row, _ = ProductTagConfig.objects.update_or_create(
            product=product,
            tag=tag,
            defaults={
                'is_active': True,
                'source_type': source_type,
            },
        )
        rows.append(row)
    return rows
