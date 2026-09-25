"""Complaint permissions and menu seed."""

from typing import Any

COMPLAINT_PERMISSIONS = [
    ('投诉查看', 'complaint:read', '投诉管理', 'read'),
    ('投诉仲裁', 'complaint:review', '投诉管理', 'review'),
    ('投诉关闭', 'complaint:close', '投诉管理', 'close'),
]


def seed_complaint_permissions(permission_model):
    permissions = {}
    for name, code, module, action in COMPLAINT_PERMISSIONS:
        perm, _ = permission_model.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'module': module,
                'action': action,
                'description': name,
            },
        )
        permissions[code] = perm
    return permissions


def seed_complaint_menu(menu_model, customer_dir, permissions):
    menu, _ = menu_model.objects.update_or_create(
        name='ComplaintList',
        defaults={
            'title': '投诉管理',
            'path': '/customers/complaints',
            'component': 'customers/ComplaintList',
            'icon': 'Warning',
            'menu_type': 'menu',
            'sort_order': 44,
            'parent': customer_dir,
            'permission': permissions.get('complaint:read'),
            'is_visible': True,
            'is_active': True,
        },
    )
    return menu


def seed_complaint_menus(
    menu_model: Any,
    permissions: dict[str, Any] | None = None,
    *,
    permission_model: Any | None = None,
) -> dict[str, Any]:
    """Upsert complaint permissions and sidebar menu (deploy / sync_menus)."""
    if permission_model is None:
        from rbac.models import Permission as permission_model

    permissions = dict(permissions or {})
    permissions.update(seed_complaint_permissions(permission_model))
    customer_dir = menu_model.objects.filter(name='CustomerDir').first()
    if customer_dir:
        seed_complaint_menu(menu_model, customer_dir, permissions)
    return permissions
