"""Tenant menu and permission seed helpers."""

from typing import Any

TENANT_PERMISSIONS: list[tuple[str, str, str, str]] = [
    ('商户查看', 'tenant:view', '商户管理', 'read'),
    ('商户新增', 'tenant:create', '商户管理', 'create'),
    ('商户审核', 'tenant:approve', '商户管理', 'approve'),
    ('商户暂停恢复', 'tenant:suspend', '商户管理', 'suspend'),
    ('商户删除', 'tenant:delete', '商户管理', 'delete'),
    ('申诉处理', 'tenant:appeal', '商户管理', 'appeal'),
    ('变更查看', 'tenant:change:view', '商户管理', 'read'),
    ('变更审核', 'tenant:change:review', '商户管理', 'approve'),
]

TENANT_DIR_MENUS = [
    'TenantDir',
    'TenantManage',
    'TenantAppealManage',
    'TenantChatWorkbench',
    'TenantPendingChanges',
]

TENANT_ROLE_PERMISSIONS: dict[str, list[str]] = {
    'ops_director': [
        'tenant:view',
        'tenant:create',
        'tenant:approve',
        'tenant:suspend',
        'tenant:appeal',
        'tenant:change:view',
        'tenant:change:review',
    ],
    'ops_manager': ['tenant:view', 'tenant:change:view'],
}


def seed_tenant_permissions(permission_model: Any) -> dict[str, Any]:
    permissions: dict[str, Any] = {}
    for name, code, module, action in TENANT_PERMISSIONS:
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


def seed_tenant_directory_menu(menu_model: Any, permissions: dict[str, Any]) -> Any:
    """Top-level 商户管理 with 商城商户 / 商户申诉 / 在线客服."""
    tenant_dir, _ = menu_model.objects.update_or_create(
        name='TenantDir',
        defaults={
            'title': '商户管理',
            'path': '/tenants',
            'icon': 'Shop',
            'menu_type': 'directory',
            'sort_order': 45,
            'parent': None,
            'is_visible': True,
            'is_active': True,
        },
    )

    menu_model.objects.update_or_create(
        name='TenantManage',
        defaults={
            'title': '商城商户',
            'path': '/tenants/list',
            'component': 'system/TenantList',
            'icon': 'Shop',
            'menu_type': 'menu',
            'sort_order': 1,
            'parent': tenant_dir,
            'permission': permissions.get('tenant:view'),
            'is_visible': True,
            'is_active': True,
        },
    )
    menu_model.objects.update_or_create(
        name='TenantAppealManage',
        defaults={
            'title': '商户申诉',
            'path': '/tenants/appeals',
            'component': 'system/AppealList',
            'icon': 'ChatLineSquare',
            'menu_type': 'menu',
            'sort_order': 2,
            'parent': tenant_dir,
            'permission': permissions.get('tenant:appeal'),
            'is_visible': True,
            'is_active': True,
        },
    )
    menu_model.objects.update_or_create(
        name='TenantChatWorkbench',
        defaults={
            'title': '在线客服',
            'path': '/tenants/chat',
            'component': 'tenants/TenantServiceWorkbench',
            'icon': 'ChatLineRound',
            'menu_type': 'menu',
            'sort_order': 3,
            'parent': tenant_dir,
            'permission': permissions.get('tenant:view'),
            'is_visible': True,
            'is_active': True,
        },
    )
    menu_model.objects.update_or_create(
        name='TenantPendingChanges',
        defaults={
            'title': '待审核变更',
            'path': '/tenants/pending-changes',
            'component': 'tenants/PendingChangesList',
            'icon': 'EditPen',
            'menu_type': 'menu',
            'sort_order': 4,
            'parent': tenant_dir,
            'permission': permissions.get('tenant:change:view'),
            'is_visible': True,
            'is_active': True,
        },
    )

    return tenant_dir


def seed_tenant_menu(menu_model: Any, _system_dir: Any, permissions: dict[str, Any]) -> Any:
    return seed_tenant_directory_menu(menu_model, permissions)


def seed_tenant_menu_migration(apps, schema_editor) -> None:
    from accounts.rbac_seed import seed_default_roles_migration

    permission_model = apps.get_model('rbac', 'Permission')
    menu_model = apps.get_model('rbac', 'Menu')
    role_model = apps.get_model('rbac', 'Role')
    permissions = seed_tenant_permissions(permission_model)
    seed_tenant_directory_menu(menu_model, permissions)

    chat = menu_model.objects.filter(name='ChatWorkbench').first()
    if chat:
        chat.title = '商城客服'
        chat.save(update_fields=['title'])

    for role_code, perm_codes in TENANT_ROLE_PERMISSIONS.items():
        role = role_model.objects.filter(code=role_code).first()
        if not role:
            continue
        role.permissions.add(*[permissions[code] for code in perm_codes if code in permissions])
    seed_default_roles_migration(apps, schema_editor)
