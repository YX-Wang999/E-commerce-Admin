"""Membership permissions, menus and default levels seed."""

from __future__ import annotations

from typing import Any

MEMBERSHIP_PERMISSIONS: list[tuple[str, str, str, str]] = [
    ('会员等级查看', 'membership:read', '会员等级', 'read'),
    ('会员等级管理', 'membership:manage', '会员等级', 'manage'),
]

DEFAULT_LEVELS = [
    {'level': 1, 'name': '普通会员', 'min_points': 0, 'discount_rate': 100, 'points_multiplier': '1.00', 'sort_order': 1},
    {'level': 2, 'name': '白银会员', 'min_points': 500, 'discount_rate': 98, 'points_multiplier': '1.20', 'sort_order': 2},
    {'level': 3, 'name': '黄金会员', 'min_points': 2000, 'discount_rate': 95, 'points_multiplier': '1.50', 'sort_order': 3},
    {'level': 4, 'name': '铂金会员', 'min_points': 8000, 'discount_rate': 92, 'points_multiplier': '2.00', 'sort_order': 4},
    {'level': 5, 'name': '钻石会员', 'min_points': 20000, 'discount_rate': 88, 'points_multiplier': '3.00', 'sort_order': 5},
]


def seed_membership_permissions(permission_model: Any) -> dict[str, Any]:
    permissions: dict[str, Any] = {}
    for name, code, module, action in MEMBERSHIP_PERMISSIONS:
        permission, _ = permission_model.objects.update_or_create(
            code=code,
            defaults={'name': name, 'module': module, 'action': action, 'description': name},
        )
        permissions[code] = permission
    return permissions


def seed_membership_menus(menu_model: Any, permissions: dict[str, Any]) -> None:
    customer_dir = menu_model.objects.filter(name='CustomerDir').first()
    if customer_dir is None:
        return

    menu_model.objects.update_or_create(
        name='MembershipLevelList',
        defaults={
            'title': '会员等级',
            'path': '/customers/membership-levels',
            'component': 'membership/LevelList',
            'icon': 'Medal',
            'menu_type': 'menu',
            'sort_order': 42,
            'parent': customer_dir,
            'permission': permissions.get('membership:read'),
            'is_visible': True,
            'is_active': True,
        },
    )


def seed_default_member_levels(level_model: Any) -> None:
    for item in DEFAULT_LEVELS:
        level_model.objects.update_or_create(
            level=item['level'],
            defaults={
                'name': item['name'],
                'min_points': item['min_points'],
                'discount_rate': item['discount_rate'],
                'points_multiplier': item['points_multiplier'],
                'sort_order': item['sort_order'],
                'description': f"{item['name']}专属权益",
                'is_active': True,
            },
        )


def seed_membership_migration(apps, schema_editor) -> None:
    permission_model = apps.get_model('rbac', 'Permission')
    menu_model = apps.get_model('rbac', 'Menu')
    level_model = apps.get_model('membership', 'MemberLevel')
    permissions = seed_membership_permissions(permission_model)
    seed_default_member_levels(level_model)
    seed_membership_menus(menu_model, permissions)
