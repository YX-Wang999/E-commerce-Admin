"""Points permissions, menus and demo data seed."""

from decimal import Decimal
from typing import Any

from customers.models import Customer
from points.models import PointsAccount, PointsRule
from points.services import get_or_create_account

POINTS_PERMISSIONS: list[tuple[str, str, str, str]] = [
    ('积分查看', 'points:read', '积分管理', 'read'),
    ('积分调整', 'points:adjust', '积分管理', 'adjust'),
    ('积分规则', 'points:rule', '积分管理', 'rule'),
]

EARN_RULES: list[dict[str, Any]] = [
    {'code': 'sign_in', 'name': '每日签到', 'description': '每日首次签到', 'default_value': 5, 'min_value': 1, 'max_value': 50, 'sort_order': 10},
    {'code': 'sign_in_streak', 'name': '连续签到奖励', 'description': '连续签到第N天，积分翻倍', 'default_value': 5, 'min_value': 1, 'max_value': 50, 'sort_order': 20},
    {'code': 'order_rate', 'name': '消费积分', 'description': '每消费 10 元 = 1 积分', 'default_value': Decimal('0.1'), 'min_value': Decimal('0.01'), 'max_value': 10, 'sort_order': 30},
    {'code': 'order_bonus', 'name': '订单奖励', 'description': '订单完成额外奖励', 'default_value': 20, 'min_value': 0, 'max_value': 200, 'sort_order': 40},
    {'code': 'review', 'name': '评价奖励', 'description': '提交商品评价', 'default_value': 10, 'min_value': 0, 'max_value': 100, 'sort_order': 50},
    {'code': 'review_photo', 'name': '带图评价', 'description': '评价附带图片', 'default_value': 20, 'min_value': 0, 'max_value': 200, 'sort_order': 60},
    {'code': 'review_video', 'name': '带视频评价', 'description': '评价附带视频', 'default_value': 30, 'min_value': 0, 'max_value': 300, 'sort_order': 70},
    {'code': 'first_order', 'name': '首单奖励', 'description': '用户首次下单', 'default_value': 50, 'min_value': 0, 'max_value': 500, 'sort_order': 80},
    {'code': 'first_review', 'name': '首次评价', 'description': '用户首次评价', 'default_value': 30, 'min_value': 0, 'max_value': 300, 'sort_order': 90},
    {'code': 'birthday', 'name': '生日奖励', 'description': '生日当天签到', 'default_value': 50, 'min_value': 0, 'max_value': 500, 'sort_order': 100},
    {'code': 'invite_friend', 'name': '邀请好友', 'description': '邀请好友注册并消费', 'default_value': 100, 'min_value': 0, 'max_value': 1000, 'sort_order': 110},
    {'code': 'share', 'name': '分享商品', 'description': '分享商品链接/海报', 'default_value': 5, 'min_value': 0, 'max_value': 50, 'sort_order': 120},
    {'code': 'profile_complete', 'name': '完善资料', 'description': '完善全部个人信息', 'default_value': 30, 'min_value': 0, 'max_value': 200, 'sort_order': 130},
    {'code': 'bind_phone', 'name': '绑定手机', 'description': '首次绑定手机号', 'default_value': 20, 'min_value': 0, 'max_value': 100, 'sort_order': 140},
    {'code': 'bind_email', 'name': '绑定邮箱', 'description': '首次绑定邮箱', 'default_value': 10, 'min_value': 0, 'max_value': 50, 'sort_order': 150},
    {'code': 'follow_shop', 'name': '关注店铺', 'description': '首次关注店铺', 'default_value': 10, 'min_value': 0, 'max_value': 50, 'sort_order': 160},
]

REDEEM_RULES: list[dict[str, Any]] = [
    {'code': 'redeem_rate', 'name': '积分抵扣比例', 'description': '10 积分 = 1 元', 'default_value': 10, 'min_value': 1, 'max_value': 1000, 'sort_order': 10},
    {'code': 'redeem_max_rate', 'name': '最大抵扣比例', 'description': '最多可抵订单金额的 %', 'default_value': 30, 'min_value': 10, 'max_value': 100, 'sort_order': 20},
    {'code': 'redeem_min_amount', 'name': '最低抵扣金额', 'description': '订单满 N 元可使用', 'default_value': 10, 'min_value': 0, 'max_value': 100, 'sort_order': 30},
]


def _upsert_rule(rule_model: Any, item: dict[str, Any], rule_type: str) -> None:
    defaults = {
        'name': item['name'],
        'description': item.get('description', ''),
        'rule_type': rule_type,
        'default_value': item['default_value'],
        'min_value': item.get('min_value'),
        'max_value': item.get('max_value'),
        'sort_order': item.get('sort_order', 0),
        'is_system': True,
        'is_active': True,
    }
    row, created = rule_model.objects.update_or_create(code=item['code'], defaults=defaults)
    if created or not row.current_value:
        row.current_value = item['default_value']
        row.save(update_fields=['current_value', 'points_value', 'updated_at'])


def seed_points_rules(rule_model: Any) -> None:
    """Seed default points rules."""
    for item in EARN_RULES:
        _upsert_rule(rule_model, item, PointsRule.RULE_EARN)
    for item in REDEEM_RULES:
        _upsert_rule(rule_model, item, PointsRule.RULE_REDEEM)


def seed_points_permissions(permission_model: Any) -> dict[str, Any]:
    """Create points permissions."""
    permissions: dict[str, Any] = {}
    for name, code, module, action in POINTS_PERMISSIONS:
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


def seed_points_accounts(account_model: Any, customer_model: Any) -> None:
    """Backfill points accounts from customers."""
    for customer in customer_model.objects.filter(is_active=True):
        get_or_create_account(customer)


def seed_points_menus(menu_model: Any, system_dir: Any, permissions: dict[str, Any]) -> None:
    """Create points management menus under system."""
    points_dir, _ = menu_model.objects.update_or_create(
        name='PointsDir',
        defaults={
            'title': '积分管理',
            'path': '/system/points',
            'icon': 'Coin',
            'menu_type': 'directory',
            'sort_order': 97,
            'parent': system_dir,
            'permission': permissions.get('points:read'),
            'is_visible': True,
            'is_active': True,
        },
    )
    menu_defs = [
        ('PointsManage', '平台积分', '/system/points', 'system/points/PointsManageView', 'Wallet', 98, points_dir, 'points:read'),
        ('PointsRules', '平台积分规则', '/system/points-rules', 'system/points/PointsRulesView', 'Setting', 99, points_dir, 'points:rule'),
        ('SellerPointsMonitor', '商家积分监控', '/system/seller-points', 'system/points/SellerPointsMonitorView', 'DataAnalysis', 100, points_dir, 'points:read'),
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


def seed_points_migration(apps, schema_editor) -> None:
    """Migration hook: points menu, permissions, rules, accounts."""
    from accounts.rbac_seed import seed_default_roles_migration

    permission_model = apps.get_model('rbac', 'Permission')
    menu_model = apps.get_model('rbac', 'Menu')
    rule_model = apps.get_model('points', 'PointsRule')
    customer_model = apps.get_model('customers', 'Customer')
    permissions = seed_points_permissions(permission_model)
    system_dir = menu_model.objects.filter(name='System').first()
    if system_dir:
        seed_points_menus(menu_model, system_dir, permissions)
    seed_points_rules(rule_model)
    account_model = apps.get_model('points', 'PointsAccount')
    for customer in customer_model.objects.filter(is_active=True):
        account_model.objects.update_or_create(
            customer=customer,
            defaults={'balance': customer.points, 'total_earned': customer.points, 'total_spent': 0},
        )
    seed_default_roles_migration(apps, schema_editor)
