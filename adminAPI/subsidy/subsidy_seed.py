"""Subsidy permissions, menus and demo policy seed."""

from __future__ import annotations

from typing import Any

from django.utils import timezone

SUBSIDY_PERMISSIONS: list[tuple[str, str, str, str]] = [
    ('国补查看', 'subsidy:read', '国补管理', 'read'),
    ('国补创建', 'subsidy:create', '国补管理', 'create'),
    ('国补编辑', 'subsidy:update', '国补管理', 'update'),
    ('国补审核', 'subsidy:approve', '国补管理', 'approve'),
]


def seed_subsidy_permissions(permission_model: Any) -> dict[str, Any]:
    permissions: dict[str, Any] = {}
    for name, code, module, action in SUBSIDY_PERMISSIONS:
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


def seed_subsidy_menus(menu_model: Any, permissions: dict[str, Any]) -> None:
    subsidy_dir, _ = menu_model.objects.update_or_create(
        name='SubsidyDir',
        defaults={
            'title': '国补数据监控',
            'path': '/subsidy',
            'icon': 'Medal',
            'menu_type': 'directory',
            'sort_order': 27,
            'parent': None,
            'permission': permissions.get('subsidy:read'),
            'is_visible': True,
            'is_active': True,
        },
    )
    menu_defs = [
        (
            'SubsidyPolicyList',
            '政策配置',
            '/subsidy/policies',
            'subsidy/PolicyList',
            'Document',
            1,
            subsidy_dir,
            'subsidy:read',
        ),
        (
            'SubsidyProductReview',
            '备案状态监控',
            '/subsidy/filings',
            'subsidy/FilingMonitorList',
            'Checked',
            2,
            subsidy_dir,
            'subsidy:read',
        ),
        (
            'SubsidyStats',
            '订单上报统计',
            '/subsidy/stats',
            'subsidy/StatsView',
            'DataAnalysis',
            3,
            subsidy_dir,
            'subsidy:read',
        ),
    ]
    for name, title, path, component, icon, sort_order, parent, perm_code in menu_defs:
        menu_model.objects.update_or_create(
            name=name,
            defaults={
                'title': title,
                'path': path,
                'component': component,
                'icon': icon,
                'menu_type': 'menu',
                'sort_order': sort_order,
                'parent': parent,
                'permission': permissions.get(perm_code),
                'is_visible': True,
                'is_active': True,
            },
        )


def seed_default_subsidy_policy(policy_model: Any) -> None:
    now = timezone.now()
    policy_model.objects.get_or_create(
        name='国家补贴通用政策',
        defaults={
            'description': '参与国补的商品需完成政府备案，补贴标准以政府政策为准。',
            'subsidy_type': 'percent',
            'subsidy_value': 20,
            'max_subsidy': 2000,
            'is_active': True,
            'start_time': now,
        },
    )


def seed_subsidy_migration(apps, schema_editor) -> None:
    permission_model = apps.get_model('rbac', 'Permission')
    menu_model = apps.get_model('rbac', 'Menu')
    policy_model = apps.get_model('subsidy', 'SubsidyPolicy')
    permissions = seed_subsidy_permissions(permission_model)
    seed_subsidy_menus(menu_model, permissions)
    seed_default_subsidy_policy(policy_model)

    role_model = apps.get_model('rbac', 'Role')
    super_admin = role_model.objects.filter(code='super_admin').first()
    if super_admin:
        for perm in permissions.values():
            super_admin.permissions.add(perm)
        for menu in menu_model.objects.filter(name__in=['SubsidyDir', 'SubsidyPolicyList', 'SubsidyProductReview', 'SubsidyStats']):
            super_admin.menus.add(menu)
