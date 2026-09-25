"""Department menu and permission seed helpers."""

from typing import Any

DEFAULT_DEPARTMENTS: list[tuple[str, str]] = [
    ('tech', '技术部'),
    ('ops', '运营部'),
    ('sales', '销售部'),
    ('cs', '客服部'),
    ('warehouse', '仓储部'),
    ('hr', '人事部'),
    ('finance', '财务部'),
]

DEPARTMENT_PERMISSIONS: list[tuple[str, str, str, str]] = [
    ('部门查看', 'department:read', '部门管理', 'read'),
    ('部门新增', 'department:create', '部门管理', 'create'),
    ('部门修改', 'department:update', '部门管理', 'update'),
    ('部门删除', 'department:delete', '部门管理', 'delete'),
]

DEMO_USER_DEPARTMENTS: dict[str, str] = {
    'ops_director': 'ops',
    'ops_manager': 'ops',
    'ops_staff': 'ops',
    'cs_manager': 'cs',
    'cs_staff': 'cs',
    'warehouse': 'warehouse',
    'data_analyst': 'tech',
    'dept_manager': 'hr',
    'employee': 'sales',
}


def seed_department_permissions(permission_model: Any) -> dict[str, Any]:
    """Create department CRUD permissions."""
    permissions: dict[str, Any] = {}
    for name, code, module, action in DEPARTMENT_PERMISSIONS:
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


def seed_department_menu(menu_model: Any, system_dir: Any, permissions: dict[str, Any]) -> Any:
    """Create department management menu under system directory."""
    menu, _ = menu_model.objects.update_or_create(
        name='DepartmentManage',
        defaults={
            'title': '部门管理',
            'path': '/system/department',
            'component': 'system/DepartmentView',
            'icon': 'OfficeBuilding',
            'menu_type': 'menu',
            'sort_order': 90,
            'parent': system_dir,
            'permission': permissions.get('department:read'),
            'is_visible': True,
            'is_active': True,
        },
    )
    return menu


def seed_default_departments(department_model: Any) -> dict[str, Any]:
    """Create default top-level departments."""
    departments: dict[str, Any] = {}
    for code, name in DEFAULT_DEPARTMENTS:
        department, _ = department_model.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'is_active': True,
            },
        )
        departments[code] = department
    return departments


def assign_department_memberships(
    user_model: Any,
    departments: dict[str, Any],
) -> None:
    """Assign demo users to departments and set department managers."""
    hr_dept = departments.get('hr')
    cs_dept = departments.get('cs')
    hr_manager = user_model.objects.filter(username='dept_manager').first()
    cs_manager = user_model.objects.filter(username='cs_manager').first()

    if hr_manager and hr_dept:
        hr_dept.manager = hr_manager
        hr_dept.save(update_fields=['manager'])
        hr_manager.department = hr_dept
        hr_manager.save(update_fields=['department'])

    if cs_manager and cs_dept:
        cs_dept.manager = cs_manager
        cs_dept.save(update_fields=['manager'])
        cs_manager.department = cs_dept
        cs_manager.save(update_fields=['department'])

    skip_users = {'dept_manager', 'cs_manager'}
    for username, dept_code in DEMO_USER_DEPARTMENTS.items():
        if username in skip_users:
            continue
        user = user_model.objects.filter(username=username).first()
        department = departments.get(dept_code)
        if user and department:
            user.department = department
            user.save(update_fields=['department'])


def seed_department_menu_migration(apps, schema_editor) -> None:
    """Migration hook: permissions, menu, departments and role refresh."""
    from accounts.rbac_seed import seed_default_roles_migration

    permission_model = apps.get_model('rbac', 'Permission')
    menu_model = apps.get_model('rbac', 'Menu')
    department_model = apps.get_model('accounts', 'Department')
    user_model = apps.get_model('accounts', 'User')
    permissions = seed_department_permissions(permission_model)
    system_dir = menu_model.objects.filter(name='System').first()
    if system_dir:
        seed_department_menu(menu_model, system_dir, permissions)
    departments = seed_default_departments(department_model)
    assign_department_memberships(user_model, departments)
    seed_default_roles_migration(apps, schema_editor)
