"""Shop rating permissions and admin menu seed."""

from __future__ import annotations

from typing import Any

SHOP_RATING_PERMISSIONS: list[tuple[str, str, str, str]] = [
    ('店铺评分查看', 'shop_rating:read', '店铺评分', 'read'),
    ('评分调整审核', 'shop_rating:review', '店铺评分', 'review'),
]


def seed_shop_rating_permissions(permission_model: Any) -> dict[str, Any]:
    permissions: dict[str, Any] = {}
    for name, code, module, action in SHOP_RATING_PERMISSIONS:
        permission, _ = permission_model.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'module': module,
                'action': action,
                'description': name,
            },
        )
        permissions[code] = permission
    return permissions


def seed_shop_rating_menus(
    menu_model: Any,
    permissions: dict[str, Any],
    *,
    tenant_dir: Any | None = None,
) -> None:
    """Create shop rating menu under 商户管理."""
    tenant_dir = tenant_dir or menu_model.objects.filter(name='TenantDir').first()
    if tenant_dir is None:
        return

    menu_model.objects.update_or_create(
        name='ShopRatingList',
        defaults={
            'title': '店铺评分',
            'path': '/tenants/shop-ratings',
            'component': 'shop-rating/ShopRatingListView',
            'icon': 'Star',
            'menu_type': 'menu',
            'sort_order': 5,
            'parent': tenant_dir,
            'permission': permissions.get('shop_rating:read'),
            'is_visible': True,
            'is_active': True,
        },
    )
