"""Seed shop closure admin menu."""

from typing import Any


def seed_closure_menus(menu_model: Any, system_dir: Any, permissions: dict[str, Any]) -> None:
    if system_dir is None:
        system_dir = menu_model.objects.filter(name='System').first()
    if system_dir is None:
        return

    menu_model.objects.update_or_create(
        name='ClosureList',
        defaults={
            'title': '店铺注销',
            'path': '/system/closures',
            'component': 'system/closure/ClosureListView',
            'icon': 'SwitchButton',
            'menu_type': 'menu',
            'sort_order': 46,
            'parent': system_dir,
            'permission': permissions.get('tenant:view'),
            'is_visible': True,
            'is_active': True,
        },
    )
