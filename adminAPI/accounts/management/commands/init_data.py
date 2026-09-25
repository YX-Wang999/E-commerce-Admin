"""Initialize default admin and e-commerce data."""

import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.demo_credentials import DEMO_PASSWORD
from accounts.org_seed import assign_demo_supervisors
from accounts.department_seed import (
    assign_department_memberships,
    seed_default_departments,
)
from accounts.ecommerce_seed import (
    create_ecommerce_menus,
    create_ecommerce_permissions,
    seed_ecommerce_demo_data,
)
from accounts.rbac_seed import seed_default_roles
from accounts.models import Department
from rbac.models import Menu, Permission, Role
from system.models import SystemSetting

logger = logging.getLogger(__name__)
User = get_user_model()

# 9 个演示账号：admin + 8 个业务角色（不含「编辑」等废弃角色）
DEMO_USERS = [
    ('ops_director', '运营总监', 'ops_director'),
    ('ops_manager', '运营主管', 'ops_manager'),
    ('ops_staff', '运营专员', 'ops_staff'),
    ('cs_staff', '客服专员', 'cs_staff'),
    ('warehouse', '仓库管理员', 'warehouse_manager'),
    ('data_analyst', '数据分析师', 'data_analyst'),
    ('dept_manager', '人事部经理', 'dept_manager'),
    ('cs_manager', '客服部经理', 'dept_manager'),
    ('employee', '普通员工', 'employee'),
]

SYSTEM_PERMISSIONS = [
    ('用户查看', 'user:read', '用户管理', 'read'),
    ('用户新增', 'user:create', '用户管理', 'create'),
    ('用户修改', 'user:update', '用户管理', 'update'),
    ('用户删除', 'user:delete', '用户管理', 'delete'),
    ('角色查看', 'role:read', '角色管理', 'read'),
    ('角色新增', 'role:create', '角色管理', 'create'),
    ('角色修改', 'role:update', '角色管理', 'update'),
    ('角色删除', 'role:delete', '角色管理', 'delete'),
    ('菜单查看', 'menu:read', '菜单管理', 'read'),
    ('菜单新增', 'menu:create', '菜单管理', 'create'),
    ('菜单修改', 'menu:update', '菜单管理', 'update'),
    ('菜单删除', 'menu:delete', '菜单管理', 'delete'),
    ('日志查看', 'audit:read', '操作日志', 'read'),
    ('设置查看', 'setting:read', '系统设置', 'read'),
    ('设置修改', 'setting:update', '系统设置', 'update'),
    ('部门查看', 'department:read', '部门管理', 'read'),
    ('部门新增', 'department:create', '部门管理', 'create'),
    ('部门修改', 'department:update', '部门管理', 'update'),
    ('部门删除', 'department:delete', '部门管理', 'delete'),
    ('组织架构查看', 'org:read', '组织架构', 'read'),
    ('财务汇总查看', 'report:finance', '数据报表', 'finance'),
]


class Command(BaseCommand):
    """Seed permissions, menus, roles, admin account and demo data."""

    help = 'Initialize RBAC and e-commerce demo data'

    def handle(self, *args, **options) -> None:
        """Run initialization."""
        try:
            permissions = self._create_system_permissions()
            permissions.update(create_ecommerce_permissions())
            from tenants.tenant_seed import seed_tenant_directory_menu, seed_tenant_permissions

            permissions.update(seed_tenant_permissions(Permission))
            from subsidy.subsidy_seed import seed_subsidy_permissions, seed_subsidy_menus, seed_default_subsidy_policy
            from subsidy.models import SubsidyPolicy

            permissions.update(seed_subsidy_permissions(Permission))
            from membership.membership_seed import (
                seed_default_member_levels,
                seed_membership_menus,
                seed_membership_permissions,
            )
            from membership.models import MemberLevel

            permissions.update(seed_membership_permissions(Permission))
            create_ecommerce_menus(permissions)
            seed_subsidy_menus(Menu, permissions)
            seed_membership_menus(Menu, permissions)
            from accounts.menu_sync import sync_all_menus
            from tag_system.tag_seed import seed_tags

            sync_all_menus(refresh_roles=False)
            seed_tags()
            seed_default_subsidy_policy(SubsidyPolicy)
            seed_default_member_levels(MemberLevel)
            seed_tenant_directory_menu(Menu, permissions)
            from shop_rating.shop_rating_seed import seed_shop_rating_menus, seed_shop_rating_permissions

            permissions.update(seed_shop_rating_permissions(Permission))
            seed_shop_rating_menus(Menu, permissions)
            permissions = {item.code: item for item in Permission.objects.all()}
            menus = {item.name: item for item in Menu.objects.all()}
            roles = seed_default_roles(permissions, menus, Role)
            self._cleanup_obsolete_roles(roles)
            self._create_admin_user(roles['super_admin'])
            departments = seed_default_departments(Department)
            self._create_demo_users(roles)
            assign_department_memberships(User, departments)
            assign_demo_supervisors(User)
            self._cleanup_obsolete_demo_users()
            self._create_system_settings()
            seed_ecommerce_demo_data()
            from accounts.tenant_demo_seed import seed_demo_seller_staff

            seed_demo_seller_staff()
            self._print_success()
        except Exception:
            logger.exception('Init data failed')
            raise

    def _create_system_permissions(self) -> dict[str, Permission]:
        """Create system permissions."""
        permissions: dict[str, Permission] = {}
        for name, code, module, action in SYSTEM_PERMISSIONS:
            permission, _ = Permission.objects.update_or_create(
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

    def _create_admin_user(self, super_admin_role: Role) -> None:
        """Create default admin user."""
        user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'nickname': '超级管理员',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            },
        )
        user.set_password('admin123456')
        user.is_first_login = False
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        user.roles.set([super_admin_role])

    def _create_demo_users(self, roles: dict[str, Role]) -> None:
        """Create demo users for each business role."""
        for username, nickname, role_code in DEMO_USERS:
            role = roles.get(role_code)
            if not role:
                logger.warning('Demo user skipped, role not found: %s', role_code)
                continue
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'nickname': nickname,
                    'is_staff': False,
                    'is_superuser': False,
                    'is_active': True,
                    'is_first_login': False,
                },
            )
            user.nickname = nickname
            user.set_password(DEMO_PASSWORD)
            user.is_staff = False
            user.is_superuser = False
            user.is_active = True
            user.is_first_login = False
            user.save()
            user.roles.set([role])

    def _cleanup_obsolete_roles(self, roles: dict[str, Role]) -> None:
        """Remove roles that are no longer part of the nine-role matrix."""
        Role.objects.exclude(code__in=roles.keys()).filter(
            code__in=['editor'],
        ).delete()

    def _cleanup_obsolete_demo_users(self) -> None:
        """Remove legacy demo accounts such as the deprecated editor role user."""
        User.objects.filter(username__in=['editor']).delete()

    def _print_success(self) -> None:
        """Print initialization summary with demo accounts."""
        lines = [
            f'初始化完成。演示密码均为 {DEMO_PASSWORD}',
            '',
            '【平台后台 admin.wangyixiang.xyz】用户名 + 密码：',
            '  admin（超级管理员）',
        ]
        for username, nickname, _ in DEMO_USERS:
            lines.append(f'  {username}（{nickname}）')
        lines.extend([
            '',
            '【商户后台 seller.wangyixiang.xyz】手机号 + 密码：',
            '  13900000001（张三的店）',
            '  13900000002（李四的店）',
            '',
            '【用户商城 customer.wangyixiang.xyz】手机号 + 密码：',
            '  13800000000 ~ 13800000004',
        ])
        self.stdout.write(self.style.SUCCESS('\n'.join(lines)))

    def _create_system_settings(self) -> None:
        """Create default system settings."""
        settings_defs = [
            ('site_title', '电商公司管理后台', SystemSetting.VALUE_TYPE_STRING, '网站标题'),
            ('site_logo', '', SystemSetting.VALUE_TYPE_FILE, '网站 Logo'),
            ('icp_number', '', SystemSetting.VALUE_TYPE_STRING, '备案号'),
            (
                'tenant_name_sensitive_words',
                '测试,admin,官方,平台,旗舰店',
                SystemSetting.VALUE_TYPE_STRING,
                '商户名称敏感词（逗号分隔）',
            ),
        ]
        for key, value, value_type, description in settings_defs:
            SystemSetting.objects.update_or_create(
                key=key,
                defaults={
                    'value': value,
                    'value_type': value_type,
                    'description': description,
                },
            )
        from system.role_display_names import seed_role_display_names_setting
        seed_role_display_names_setting()
