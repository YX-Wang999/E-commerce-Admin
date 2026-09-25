"""Seed approval workbench menu."""

from typing import Any


def seed_approval_menus(menu_model: Any, permissions: dict[str, Any] | None = None) -> None:
    permissions = permissions or {}
    menu_model.objects.update_or_create(
        name='ApprovalWorkbench',
        defaults={
            'title': '审核工作台',
            'path': '/approvals',
            'component': 'approval/ApprovalWorkbench',
            'icon': 'Checked',
            'menu_type': 'menu',
            'sort_order': 5,
            'parent': None,
            'permission': permissions.get('tenant:approve'),
            'is_visible': True,
            'is_active': True,
        },
    )
