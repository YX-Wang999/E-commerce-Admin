"""Default RBAC seed helpers for init_data and migrations."""

from typing import Any

PROMOTION_MENUS = ['PromotionDir', 'SeckillList', 'GroupBuyList', 'CouponList', 'SuperDiscountList']
PRODUCT_MENUS = ['ProductDir', 'ProductList', 'CategoryList', 'BrandList']
ORDER_MENUS_FULL = ['OrderDir', 'OrderList', 'RefundList', 'LogisticsList']
ORDER_MENUS_WAREHOUSE = ['OrderDir', 'LogisticsList']
ORDER_MENUS_READ = ['OrderDir', 'OrderList']
CUSTOMER_MENUS = ['CustomerDir', 'CustomerList', 'MembershipLevelList', 'FeedbackList', 'ComplaintList']
CUSTOMER_MENUS_READ = ['CustomerDir', 'CustomerList', 'ComplaintList']
CHAT_MENUS = ['ChatWorkbench']
REPORT_MENUS_BUSINESS = [
    'ReportDir',
    'ReportSales',
    'ReportProductRank',
    'ReportCustomer',
    'ReportPromotion',
]
REPORT_MENUS_FULL = [*REPORT_MENUS_BUSINESS, 'ReportFinance']
REPORT_MENUS = REPORT_MENUS_BUSINESS
SYSTEM_FULL = ['System', 'OrgChart', 'DepartmentManage', 'UserManage', 'RoleManage', 'MenuManage', 'AuditLog', 'SystemSetting', 'AnnouncementList', 'PointsDir', 'PointsManage', 'PointsRules', 'SellerPointsMonitor', 'TagSystemDir', 'TagList', 'TagTenantReview', 'ClosureList', 'ApprovalWorkbench']
TENANT_MENUS = ['TenantDir', 'TenantManage', 'TenantAppealManage', 'TenantChatWorkbench', 'TenantPendingChanges', 'ShopRatingList']
SUBSIDY_MENUS = ['SubsidyDir', 'SubsidyPolicyList', 'SubsidyProductReview', 'SubsidyStats']
TAG_MENUS = ['TagSystemDir', 'TagList', 'TagTenantReview']
CLOSURE_MENUS = ['ClosureList']
POINTS_MENUS_READ = ['PointsDir', 'PointsManage', 'SellerPointsMonitor']
POINTS_MENUS_FULL = ['PointsDir', 'PointsManage', 'PointsRules', 'SellerPointsMonitor']
SYSTEM_DEPT = ['System', 'UserManage', 'AuditLog', 'OrgChart']

ROLE_MATRIX: dict[str, dict[str, Any]] = {
    'super_admin': {
        'name': '超级管理员',
        'description': '系统总控，拥有全部菜单与权限',
        'menu_keys': '__all__',
        'permission_codes': '__all__',
    },
    'ops_director': {
        'name': '运营总监',
        'description': '商品/订单/客户/报表全览，促销审批与优惠券发布',
        'menu_keys': [
            'Dashboard',
            *PRODUCT_MENUS,
            *ORDER_MENUS_FULL,
            *CUSTOMER_MENUS,
            *CHAT_MENUS,
            *PROMOTION_MENUS,
            *SUBSIDY_MENUS,
            *REPORT_MENUS_FULL,
            'OrgChart',
            *TENANT_MENUS,
            'AnnouncementList',
            *POINTS_MENUS_FULL,
            *TAG_MENUS,
            *CLOSURE_MENUS,
            'ApprovalWorkbench',
        ],
        'permission_codes': [
            'product:read', 'product:create', 'product:update', 'product:delete',
            'order:read', 'order:update', 'order:ship',
            'customer:read', 'customer:update',
            'feedback:read',
            'chat:read', 'chat:reply', 'chat:assign', 'chat:close',
            'points:read', 'points:adjust', 'points:rule',
            'announcement:read', 'announcement:create', 'announcement:update',
            'announcement:delete', 'announcement:publish',
            'promotion:read', 'promotion:approve', 'promotion:cancel',
            'coupon:read', 'coupon:publish',
            'report:read', 'report:finance',
            'inventory:read',
            'org:read',
            'tenant:view', 'tenant:create', 'tenant:approve', 'tenant:suspend', 'tenant:appeal',
            'tenant:change:view', 'tenant:change:review',
            'complaint:read', 'complaint:review', 'complaint:close',
            'subsidy:read', 'subsidy:create', 'subsidy:update', 'subsidy:approve',
            'shop_rating:read', 'shop_rating:review',
            'membership:read', 'membership:manage',
        ],
    },
    'ops_manager': {
        'name': '运营主管',
        'description': '商品、订单、客户、促销创建与数据报表',
        'menu_keys': [
            'Dashboard',
            *PRODUCT_MENUS,
            *ORDER_MENUS_FULL,
            *CUSTOMER_MENUS,
            *CHAT_MENUS,
            *PROMOTION_MENUS,
            *SUBSIDY_MENUS,
            *REPORT_MENUS_BUSINESS,
            'OrgChart',
            'TenantDir',
            'TenantManage',
            'TenantPendingChanges',
            'ShopRatingList',
            'AnnouncementList',
            *POINTS_MENUS_READ,
            *TAG_MENUS,
            *CLOSURE_MENUS,
            'ApprovalWorkbench',
        ],
        'permission_codes': [
            'product:read', 'product:create', 'product:update', 'product:delete',
            'promotion:read', 'promotion:create', 'promotion:update',
            'promotion:submit', 'promotion:cancel',
            'coupon:read', 'coupon:create', 'coupon:update', 'coupon:publish',
            'order:read', 'order:update', 'order:ship',
            'customer:read', 'customer:update',
            'feedback:read',
            'chat:read', 'chat:reply', 'chat:assign', 'chat:close',
            'points:read',
            'announcement:read',
            'report:read',
            'inventory:read',
            'org:read',
            'tenant:view', 'tenant:change:view',
            'complaint:read',
            'subsidy:read',
            'shop_rating:read',
            'membership:read',
        ],
    },
    'ops_staff': {
        'name': '运营专员',
        'description': '商品维护（分类/品牌只读）、促销执行、订单发货与客户管理',
        'menu_keys': [
            'Dashboard',
            *PRODUCT_MENUS,
            *PROMOTION_MENUS,
            *ORDER_MENUS_FULL,
            *CUSTOMER_MENUS,
        ],
        'permission_codes': [
            'product:read', 'product:create', 'product:update',
            'promotion:read', 'promotion:create', 'promotion:update', 'promotion:submit',
            'coupon:read', 'coupon:create', 'coupon:update',
            'order:read', 'order:update', 'order:ship',
            'customer:read', 'customer:update',
            'feedback:read',
            'complaint:read',
        ],
    },
    'cs_staff': {
        'name': '客服专员',
        'description': '客服工作台、订单与客户只读',
        'menu_keys': [
            'Dashboard',
            *CHAT_MENUS,
            *ORDER_MENUS_READ,
            *CUSTOMER_MENUS_READ,
        ],
        'permission_codes': [
            'order:read',
            'customer:read',
            'complaint:read',
            'chat:read', 'chat:reply', 'chat:close',
        ],
    },
    'warehouse_manager': {
        'name': '仓库管理员',
        'description': '订单只读与发货操作',
        'menu_keys': [
            'Dashboard',
            *ORDER_MENUS_WAREHOUSE,
        ],
        'permission_codes': [
            'order:read', 'order:ship',
        ],
    },
    'data_analyst': {
        'name': '数据分析师',
        'description': '仪表盘、数据报表与促销只读',
        'menu_keys': [
            'Dashboard',
            *PROMOTION_MENUS,
            *REPORT_MENUS_BUSINESS,
            *SUBSIDY_MENUS,
        ],
        'permission_codes': [
            'report:read', 'promotion:read', 'coupon:read', 'subsidy:read',
        ],
    },
    'dept_manager': {
        'name': '部门经理',
        'description': '本部门用户/日志、组织架构与客服工作台',
        'menu_keys': [
            'Dashboard',
            *SYSTEM_DEPT,
            *CHAT_MENUS,
        ],
        'permission_codes': [
            'user:read', 'audit:read', 'org:read',
            'chat:read', 'chat:reply', 'chat:assign', 'chat:close',
        ],
    },
    'employee': {
        'name': '普通员工',
        'description': '仅访问仪表盘',
        'menu_keys': ['Dashboard'],
        'permission_codes': [],
    },
    'customer': {
        'name': '商城用户',
        'description': '商城注册用户，仅访问仪表盘',
        'menu_keys': ['Dashboard'],
        'permission_codes': [],
    },
}


def _resolve_items(
    keys: list[str] | str,
    mapping: dict[str, Any],
) -> list[Any]:
    """Resolve key list or __all__ to model instances."""
    if keys == '__all__':
        return list(mapping.values())
    return [mapping[key] for key in keys if key in mapping]


def seed_default_roles(
    permissions: dict[str, Any],
    menus: dict[str, Any],
    role_model: Any,
) -> dict[str, Any]:
    """Create or update default roles and assign menus/permissions."""
    roles: dict[str, Any] = {}
    for code, config in ROLE_MATRIX.items():
        role, _ = role_model.objects.update_or_create(
            code=code,
            defaults={
                'name': config['name'],
                'description': config['description'],
                'is_active': True,
            },
        )
        role.permissions.set(_resolve_items(config['permission_codes'], permissions))
        role.menus.set(_resolve_items(config['menu_keys'], menus))
        roles[code] = role
    return roles


def seed_default_roles_from_db(role_model: Any, menu_model: Any, permission_model: Any) -> None:
    """Seed roles using live ORM models."""
    permissions = {item.code: item for item in permission_model.objects.all()}
    menus = {item.name: item for item in menu_model.objects.all()}
    if 'Dashboard' not in menus:
        return
    seed_default_roles(permissions, menus, role_model)


def seed_default_roles_migration(apps, schema_editor) -> None:
    """Seed roles in migration context."""
    menu_model = apps.get_model('rbac', 'Menu')
    permission_model = apps.get_model('rbac', 'Permission')
    role_model = apps.get_model('rbac', 'Role')
    seed_default_roles_from_db(role_model, menu_model, permission_model)
