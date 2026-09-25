"""E-commerce RBAC menus, permissions and seed data."""

import logging
import random
import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from announcement.announcement_seed import ANNOUNCEMENT_PERMISSIONS, seed_demo_announcements
from announcement.models import Announcement
from customers.models import Customer
from points.models import PointsAccount, PointsRule
from points.points_seed import POINTS_PERMISSIONS, seed_points_accounts, seed_points_rules
from feedback.feedback_seed import FEEDBACK_PERMISSIONS, seed_demo_feedbacks
from chat.chat_seed import CHAT_PERMISSIONS
from feedback.models import CustomerFeedback
from orders.models import Order, OrderItem, Refund
from accounts.demo_credentials import DEMO_PASSWORD
from accounts.tenant_demo_seed import seed_demo_tenants_and_products
from products.models import Brand, Category, Product
from promotion.models import Coupon, GroupBuyActivity, SeckillActivity
from rbac.models import Menu, Permission

logger = logging.getLogger(__name__)
User = get_user_model()

CATEGORY_SEED = [
    {'name': '电子产品', 'icon': '📱', 'parent': None, 'sort_order': 1},
    {'name': '电脑整机', 'icon': '💻', 'parent': '电子产品', 'sort_order': 1},
    {'name': '笔记本电脑', 'icon': '🖥️', 'parent': '电脑整机', 'sort_order': 1},
    {'name': '台式机', 'icon': '🖥️', 'parent': '电脑整机', 'sort_order': 2},
    {'name': '手机配件', 'icon': '📱', 'parent': '电子产品', 'sort_order': 2},
    {'name': '数据线', 'icon': '🔌', 'parent': '手机配件', 'sort_order': 1},
    {'name': '充电器', 'icon': '🔋', 'parent': '手机配件', 'sort_order': 2},
    {'name': '服装鞋包', 'icon': '👗', 'parent': None, 'sort_order': 2},
    {'name': '男装', 'icon': '👕', 'parent': '服装鞋包', 'sort_order': 1},
    {'name': '女装', 'icon': '👗', 'parent': '服装鞋包', 'sort_order': 2},
    {'name': '运动鞋', 'icon': '🏃', 'parent': '服装鞋包', 'sort_order': 3},
    {'name': '食品饮料', 'icon': '🍔', 'parent': None, 'sort_order': 3},
    {'name': '休闲零食', 'icon': '🍿', 'parent': '食品饮料', 'sort_order': 1},
    {'name': '饮料冲调', 'icon': '🥤', 'parent': '食品饮料', 'sort_order': 2},
    {'name': '家居生活', 'icon': '🏠', 'parent': None, 'sort_order': 4},
    {'name': '床上用品', 'icon': '🛏️', 'parent': '家居生活', 'sort_order': 1},
    {'name': '厨房用品', 'icon': '🍳', 'parent': '家居生活', 'sort_order': 2},
]


def seed_category_tree() -> dict[str, Category]:
    """Seed multi-level category tree."""
    by_path: dict[str, Category] = {}
    for item in CATEGORY_SEED:
        parent_path = item['parent']
        parent = by_path.get(parent_path) if parent_path else None
        path = item['name'] if not parent_path else f'{parent_path} > {item["name"]}'
        category, _ = Category.objects.update_or_create(
            name=item['name'],
            parent=parent,
            defaults={
                'icon': item.get('icon', ''),
                'sort_order': item['sort_order'],
                'is_active': True,
            },
        )
        by_path[path] = category
    return by_path


ECOMMERCE_PERMISSIONS = [
    ('商品查看', 'product:read', '商品管理', 'read'),
    ('商品新增', 'product:create', '商品管理', 'create'),
    ('商品修改', 'product:update', '商品管理', 'update'),
    ('商品删除', 'product:delete', '商品管理', 'delete'),
    ('订单查看', 'order:read', '订单管理', 'read'),
    ('订单处理', 'order:update', '订单管理', 'update'),
    ('订单发货', 'order:ship', '订单管理', 'ship'),
    ('客户查看', 'customer:read', '客户管理', 'read'),
    ('客户维护', 'customer:update', '客户管理', 'update'),
    ('报表查看', 'report:read', '数据报表', 'read'),
    ('财务汇总查看', 'report:finance', '数据报表', 'finance'),
    ('库存流水查看', 'inventory:read', '商品管理', 'inventory'),
    ('秒杀查看', 'promotion:read', '促销管理', 'read'),
    ('秒杀新增', 'promotion:create', '促销管理', 'create'),
    ('秒杀修改', 'promotion:update', '促销管理', 'update'),
    ('秒杀提交审核', 'promotion:submit', '促销管理', 'submit'),
    ('秒杀审批', 'promotion:approve', '促销管理', 'approve'),
    ('秒杀终止', 'promotion:cancel', '促销管理', 'cancel'),
    ('优惠券查看', 'coupon:read', '促销管理', 'read'),
    ('优惠券新增', 'coupon:create', '促销管理', 'create'),
    ('优惠券修改', 'coupon:update', '促销管理', 'update'),
    ('优惠券发布', 'coupon:publish', '促销管理', 'publish'),
    *FEEDBACK_PERMISSIONS,
    *CHAT_PERMISSIONS,
    *ANNOUNCEMENT_PERMISSIONS,
    *POINTS_PERMISSIONS,
]


def create_ecommerce_permissions() -> dict[str, Permission]:
    """Create e-commerce permissions."""
    permissions: dict[str, Permission] = {}
    for name, code, module, action in ECOMMERCE_PERMISSIONS:
        permission, _ = Permission.objects.update_or_create(
            code=code,
            defaults={'name': name, 'module': module, 'action': action, 'description': name},
        )
        permissions[code] = permission
    return permissions


def create_ecommerce_menus(permissions: dict[str, Permission]) -> dict[str, Menu]:
    """Create e-commerce menu tree."""
    Menu.objects.filter(name='ReportView').delete()
    dashboard, _ = Menu.objects.update_or_create(
        name='Dashboard',
        defaults={
            'title': '仪表盘',
            'path': '/dashboard',
            'component': 'dashboard/DashboardView',
            'icon': 'Odometer',
            'menu_type': Menu.MENU_TYPE_MENU,
            'sort_order': 1,
            'parent': None,
        },
    )

    product_dir, _ = Menu.objects.update_or_create(
        name='ProductDir',
        defaults={
            'title': '商品管理',
            'path': '/products',
            'icon': 'Goods',
            'menu_type': Menu.MENU_TYPE_DIRECTORY,
            'sort_order': 20,
            'parent': None,
        },
    )
    order_dir, _ = Menu.objects.update_or_create(
        name='OrderDir',
        defaults={
            'title': '订单管理',
            'path': '/orders',
            'icon': 'Box',
            'menu_type': Menu.MENU_TYPE_DIRECTORY,
            'sort_order': 30,
            'parent': None,
        },
    )
    customer_dir, _ = Menu.objects.update_or_create(
        name='CustomerDir',
        defaults={
            'title': '客户管理',
            'path': '/customers',
            'icon': 'User',
            'menu_type': Menu.MENU_TYPE_DIRECTORY,
            'sort_order': 40,
            'parent': None,
        },
    )
    report_dir, _ = Menu.objects.update_or_create(
        name='ReportDir',
        defaults={
            'title': '数据报表',
            'path': '/reports',
            'icon': 'TrendCharts',
            'menu_type': Menu.MENU_TYPE_DIRECTORY,
            'sort_order': 50,
            'parent': None,
        },
    )
    promotion_dir, _ = Menu.objects.update_or_create(
        name='PromotionDir',
        defaults={
            'title': '促销管理',
            'path': '/promotions',
            'icon': 'Ticket',
            'menu_type': Menu.MENU_TYPE_DIRECTORY,
            'sort_order': 25,
            'parent': None,
        },
    )
    system_dir, _ = Menu.objects.update_or_create(
        name='System',
        defaults={
            'title': '系统管理',
            'path': '/system',
            'icon': 'Setting',
            'menu_type': Menu.MENU_TYPE_DIRECTORY,
            'sort_order': 90,
            'parent': None,
        },
    )

    child_defs = [
        ('ProductList', '商品列表', '/products/list', 'products/ProductList', 'List', 21, product_dir, 'product:read'),
        ('CategoryList', '分类管理', '/products/category', 'products/CategoryList', 'Menu', 22, product_dir, 'product:read'),
        ('BrandList', '品牌管理', '/products/brand', 'products/BrandList', 'Star', 23, product_dir, 'product:read'),
        ('SeckillList', '秒杀活动', '/promotions/seckill', 'promotion/SeckillList', 'Timer', 26, promotion_dir, 'promotion:read'),
        ('GroupBuyList', '团购活动', '/promotions/groupbuy', 'promotion/GroupBuyList', 'ShoppingCart', 27, promotion_dir, 'promotion:read'),
        ('CouponList', '优惠券', '/promotions/coupon', 'promotion/CouponList', 'Discount', 28, promotion_dir, 'coupon:read'),
        ('SuperDiscountList', '超级立减', '/promotions/super-discount', 'promotion/SuperDiscountList', 'Present', 29, promotion_dir, 'promotion:read'),
        ('OrderList', '订单列表', '/orders/list', 'orders/OrderList', 'Document', 31, order_dir, 'order:read'),
        ('RefundList', '售后管理', '/orders/refund', 'orders/RefundList', 'Warning', 32, order_dir, 'order:read'),
        ('LogisticsList', '物流管理', '/orders/logistics', 'orders/LogisticsList', 'Van', 33, order_dir, 'order:ship'),
        ('CustomerList', '会员列表', '/customers/list', 'customers/CustomerList', 'Avatar', 41, customer_dir, 'customer:read'),
        ('FeedbackList', '客户留言', '/customers/feedback', 'customers/FeedbackList', 'ChatDotRound', 42, customer_dir, 'feedback:read'),
        ('ReviewList', '商品评价', '/customers/reviews', 'customers/ReviewList', 'Comment', 43, customer_dir, 'customer:read'),
        ('ChatWorkbench', '商城客服', '/customers/chat', 'customers/CustomerServiceWorkbench', 'ChatLineRound', 44, customer_dir, 'chat:read'),
        ('ReportSales', '销售报表', '/reports/sales', 'reports/SalesReportView', 'TrendCharts', 51, report_dir, 'report:read'),
        ('ReportProductRank', '商品排行', '/reports/product-rank', 'reports/ProductRankView', 'Medal', 52, report_dir, 'report:read'),
        ('ReportCustomer', '客户分析', '/reports/customer', 'reports/CustomerAnalysisView', 'User', 53, report_dir, 'report:read'),
        ('ReportPromotion', '促销分析', '/reports/promotion', 'reports/PromotionAnalysisView', 'Ticket', 54, report_dir, 'report:read'),
        ('ReportFinance', '财务汇总', '/reports/finance', 'reports/FinanceReportView', 'Coin', 55, report_dir, 'report:finance'),
        ('DepartmentManage', '部门管理', '/system/department', 'system/DepartmentView', 'OfficeBuilding', 90, system_dir, 'department:read'),
        ('OrgChart', '组织架构图', '/org/chart', 'org/OrgChartView', 'Share', 89, system_dir, 'org:read'),
        ('UserManage', '用户管理', '/system/user', 'system/UserList', 'UserFilled', 91, system_dir, 'user:read'),
        ('RoleManage', '角色管理', '/system/role', 'system/role/RoleView', 'Key', 92, system_dir, 'role:read'),
        ('MenuManage', '菜单管理', '/system/menu', 'system/menu/MenuView', 'Menu', 93, system_dir, 'menu:read'),
        ('AuditLog', '操作日志', '/system/audit', 'system/audit/AuditView', 'Document', 94, system_dir, 'audit:read'),
        ('SystemSetting', '系统设置', '/system/setting', 'system/setting/SettingView', 'Tools', 95, system_dir, 'setting:read'),
        ('AnnouncementList', '系统公告', '/system/announcement', 'system/AnnouncementList', 'Bell', 96, system_dir, 'announcement:read'),
        ('AnnouncementCenter', '公告中心', '/announcements', 'announcements/AnnouncementCenter', 'Notification', 97, system_dir, 'announcement:read'),
    ]

    menus: dict[str, Menu] = {
        'Dashboard': dashboard,
        'ProductDir': product_dir,
        'OrderDir': order_dir,
        'CustomerDir': customer_dir,
        'ReportDir': report_dir,
        'PromotionDir': promotion_dir,
        'System': system_dir,
    }
    for name, title, path, component, icon, sort_order, parent, perm_code in child_defs:
        menu, _ = Menu.objects.update_or_create(
            name=name,
            defaults={
                'title': title,
                'path': path,
                'component': component,
                'icon': icon,
                'menu_type': Menu.MENU_TYPE_MENU,
                'sort_order': sort_order,
                'parent': parent,
                'permission': permissions.get(perm_code),
            },
        )
        menus[name] = menu
    return menus


def seed_ecommerce_demo_data() -> None:
    """Seed categories, brands, products, customers and orders."""
    categories = seed_category_tree()

    brands = {}
    for name in ['Apple', '华为', '小米', 'Nike', 'Adidas']:
        brand, _ = Brand.objects.update_or_create(name=name, defaults={'is_active': True})
        brands[name] = brand

    seed_demo_tenants_and_products(categories, brands)

    customers = []
    for idx in range(5):
        customer, _ = Customer.objects.update_or_create(
            phone=f'1380000000{idx}',
            defaults={
                'name': f'客户{idx + 1}',
                'nickname': f'客户{idx + 1}',
                'email': f'customer{idx + 1}@example.com',
                'level': random.choice([
                    Customer.LEVEL_NORMAL,
                    Customer.LEVEL_SILVER,
                    Customer.LEVEL_GOLD,
                ]),
                'points': random.randint(0, 5000),
                'is_active': True,
            },
        )
        customer.set_password(DEMO_PASSWORD)
        customer.save(update_fields=['password', 'updated_at'])
        customers.append(customer)

    products = list(Product.objects.filter(status=Product.STATUS_ON_SALE)[:10])
    ops_staff_user = User.objects.filter(username='ops_staff').first()
    statuses = [
        Order.STATUS_PAID,
        Order.STATUS_SHIPPED,
        Order.STATUS_COMPLETED,
        Order.STATUS_PAID,
        Order.STATUS_REFUNDING,
    ]
    for idx in range(10):
        customer = customers[idx % len(customers)]
        order, created = Order.objects.update_or_create(
            order_no=f'ORDSEED{idx:04d}',
            defaults={
                'customer': customer,
                'total_amount': Decimal('0'),
                'status': statuses[idx % len(statuses)],
                'address': f'上海市浦东新区测试路 {idx + 1} 号',
                'logistics_no': f'SF{uuid.uuid4().hex[:10].upper()}' if idx % 2 else '',
                'assigned_to': ops_staff_user if idx % 2 == 0 else None,
            },
        )
        if created:
            OrderItem.objects.filter(order=order).delete()
        if not order.items.exists() and products:
            product = products[idx % len(products)]
            qty = random.randint(1, 3)
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=qty,
                unit_price=product.price,
            )
            order.total_amount = product.price * qty
            order.save(update_fields=['total_amount'])

    if not Refund.objects.filter(order__order_no='ORDSEED0004').exists():
        order = Order.objects.filter(order_no='ORDSEED0004').first()
        if order:
            Refund.objects.create(
                order=order,
                reason='商品质量问题',
                amount=order.total_amount,
                status=Refund.STATUS_PENDING,
            )

    _seed_seckill_demo_data()
    _seed_groupbuy_demo_data()
    _seed_coupon_demo_data()
    seed_demo_feedbacks(CustomerFeedback, Customer)
    seed_demo_announcements(Announcement, User)
    seed_points_rules(PointsRule)
    seed_points_accounts(PointsAccount, Customer)

    logger.info('E-commerce demo data seeded')


def _seed_seckill_demo_data() -> None:
    """Seed demo seckill activities."""
    if SeckillActivity.objects.exists():
        return

    product = Product.objects.filter(name='iPhone 15', is_active=True).first()
    if not product:
        return

    manager = User.objects.filter(username='ops_manager').first()
    now = timezone.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timezone.timedelta(days=1)

    activity, created = SeckillActivity.objects.get_or_create(
        name='618 限时秒杀—iPhone 15 半价',
        defaults={
            'seckill_price': Decimal('2999.00'),
            'seckill_stock': 50,
            'per_user_limit': 1,
            'start_time': start,
            'end_time': end,
            'warmup_time': start - timezone.timedelta(minutes=30),
            'status': SeckillActivity.STATUS_PENDING,
            'created_by': manager,
        },
    )
    if created:
        activity.products.set([product])


def _seed_groupbuy_demo_data() -> None:
    """Seed demo group buy activity."""
    if GroupBuyActivity.objects.exists():
        return

    product = Product.objects.filter(name__contains='坚果').first()
    if not product:
        product = Product.objects.filter(is_active=True).first()
    if not product:
        return

    manager = User.objects.filter(username='ops_manager').first()
    now = timezone.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timezone.timedelta(days=15)

    GroupBuyActivity.objects.get_or_create(
        name='3 人成团—网红零食大礼包',
        defaults={
            'product': product,
            'group_price': Decimal('99.00'),
            'group_size': 3,
            'stock': 200,
            'per_user_limit': 5,
            'group_valid_hours': 24,
            'auto_group': True,
            'start_time': start,
            'end_time': end,
            'status': GroupBuyActivity.STATUS_PENDING,
            'created_by': manager,
        },
    )


def _seed_coupon_demo_data() -> None:
    """Seed demo coupon."""
    if Coupon.objects.exists():
        return

    manager = User.objects.filter(username='ops_manager').first()
    now = timezone.now()
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = start + timezone.timedelta(days=30)

    Coupon.objects.get_or_create(
        name='618 满减券—满 300 减 50',
        defaults={
            'coupon_type': Coupon.TYPE_FIXED,
            'discount_amount': Decimal('50.00'),
            'min_amount': Decimal('300.00'),
            'total_quantity': 1000,
            'per_user_limit': 1,
            'applicable_scope': Coupon.SCOPE_ALL,
            'valid_type': Coupon.VALID_FIXED,
            'valid_start': start,
            'valid_end': end,
            'status': Coupon.STATUS_DRAFT,
            'created_by': manager,
        },
    )
