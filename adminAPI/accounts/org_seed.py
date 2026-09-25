"""Organization chart seed helpers."""

from typing import Any

ORG_PERMISSIONS: list[tuple[str, str, str, str]] = [
    ('组织架构查看', 'org:read', '组织架构', 'read'),
]

# username -> supervisor username
DEMO_SUPERVISORS: dict[str, str | None] = {
    'admin': None,
    'ops_director': 'admin',
    'ops_manager': 'ops_director',
    'ops_staff': 'ops_manager',
    'data_analyst': 'ops_director',
    'dept_manager': 'admin',
    'cs_manager': 'ops_director',
    'cs_staff': 'cs_manager',
    'warehouse': 'admin',
    'employee': 'admin',
}


def seed_org_permissions(permission_model: Any) -> dict[str, Any]:
    """Create org chart permission."""
    permissions: dict[str, Any] = {}
    for name, code, module, action in ORG_PERMISSIONS:
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


def seed_org_menu(menu_model: Any, system_dir: Any, permissions: dict[str, Any]) -> Any:
    """Create organization chart menu under system directory."""
    menu, _ = menu_model.objects.update_or_create(
        name='OrgChart',
        defaults={
            'title': '组织架构图',
            'path': '/org/chart',
            'component': 'org/OrgChartView',
            'icon': 'Share',
            'menu_type': 'menu',
            'sort_order': 89,
            'parent': system_dir,
            'permission': permissions.get('org:read'),
            'is_visible': True,
            'is_active': True,
        },
    )
    return menu


def assign_demo_supervisors(user_model: Any) -> None:
    """Wire demo account supervisor relationships."""
    users = {
        item.username: item
        for item in user_model.objects.filter(username__in=DEMO_SUPERVISORS.keys())
    }
    for username, supervisor_name in DEMO_SUPERVISORS.items():
        user = users.get(username)
        if user is None:
            continue
        supervisor = users.get(supervisor_name) if supervisor_name else None
        if user.supervisor_id != (supervisor.id if supervisor else None):
            user.supervisor = supervisor
            user.save(update_fields=['supervisor'])


def seed_org_chart_migration(apps, schema_editor) -> None:
    """Migration hook: org permission, menu and role refresh."""
    from accounts.rbac_seed import seed_default_roles_migration

    permission_model = apps.get_model('rbac', 'Permission')
    menu_model = apps.get_model('rbac', 'Menu')
    user_model = apps.get_model('accounts', 'User')
    permissions = seed_org_permissions(permission_model)
    system_dir = menu_model.objects.filter(name='System').first()
    if system_dir:
        seed_org_menu(menu_model, system_dir, permissions)
    assign_demo_supervisors(user_model)
    seed_default_roles_migration(apps, schema_editor)
