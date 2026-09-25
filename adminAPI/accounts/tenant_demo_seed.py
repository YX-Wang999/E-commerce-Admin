"""Demo merchants and tenant-scoped products for multi-store storefront."""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.demo_credentials import DEMO_PASSWORD
from products.models import Brand, Category, Product
from tenants.models import Tenant, TenantStaff

STORE_A_PRODUCTS = [
    ('iPhone 15', '电子产品 > 手机配件', 'Apple', '5999.00', 120),
    ('AirPods Pro', '电子产品 > 手机配件', 'Apple', '1299.00', 200),
    ('MacBook Pro 14', '电子产品 > 笔记本电脑', 'Apple', '9999.00', 45),
    ('iPad Air', '电子产品 > 手机配件', 'Apple', '3499.00', 80),
    ('Apple Watch S9', '电子产品 > 手机配件', 'Apple', '2999.00', 90),
    ('华为 Mate 60', '电子产品 > 手机配件', '华为', '4999.00', 75),
    ('小米 14 Ultra', '电子产品 > 手机配件', '小米', '4299.00', 110),
    ('MagSafe 充电器', '电子产品 > 充电器', 'Apple', '329.00', 300),
]

STORE_B_PRODUCTS = [
    ('Nike Air Max 90', '服装鞋包 > 运动鞋', 'Nike', '899.00', 180),
    ('Adidas Ultra Boost', '服装鞋包 > 运动鞋', 'Adidas', '799.00', 160),
    ('纯棉圆领 T 恤', '服装鞋包 > 男装', 'Nike', '199.00', 320),
    ('修身牛仔裤', '服装鞋包 > 男装', 'Adidas', '299.00', 240),
    ('轻薄羽绒服', '服装鞋包 > 女装', 'Nike', '599.00', 150),
    ('运动休闲裤', '服装鞋包 > 男装', 'Adidas', '259.00', 210),
    ('跑步鞋 Pro', '服装鞋包 > 运动鞋', 'Nike', '699.00', 130),
    ('帆布双肩包', '服装鞋包 > 女装', 'Adidas', '399.00', 95),
]

PLATFORM_PRODUCTS = [
    ('平台自营有机牛奶 1L', '食品饮料 > 饮料冲调', '小米', '12.90', 500),
    ('平台自营坚果礼盒', '食品饮料 > 休闲零食', '华为', '88.00', 300),
    ('平台自营记忆枕', '家居生活 > 床上用品', '小米', '129.00', 90),
    ('平台自营四件套', '家居生活 > 床上用品', '华为', '299.00', 60),
    ('平台自营厨房收纳套装', '家居生活 > 厨房用品', '小米', '159.00', 120),
]

DEMO_TENANTS = [
    {
        'code': 'store_a',
        'name': '张三的店',
        'logo': 'https://img.yzcdn.cn/vant/cat.jpeg',
        'contact_name': '张三',
        'contact_phone': '13900000001',
        'contact_email': 'store_a@example.com',
        'address': '深圳市南山区科技园',
        'config': {
            'intro': '主营手机、电脑、耳机等数码电子产品，正品保障，售后无忧。',
            'rating': 4.8,
        },
        'products': STORE_A_PRODUCTS,
    },
    {
        'code': 'store_b',
        'name': '李四的店',
        'logo': 'https://fastly.jsdelivr.net/npm/@vant/assets/apple-2.jpeg',
        'contact_name': '李四',
        'contact_phone': '13900000002',
        'contact_email': 'store_b@example.com',
        'address': '杭州市余杭区未来科技城',
        'config': {
            'intro': '专注运动鞋、休闲服饰与箱包，潮流好物每日上新。',
            'rating': 4.7,
        },
        'products': STORE_B_PRODUCTS,
    },
]


def _upsert_product(
    *,
    name: str,
    category: Category,
    brand: Brand,
    price: str,
    stock: int,
    tenant: Tenant | None,
) -> None:
    Product.objects.update_or_create(
        name=name,
        tenant=tenant,
        defaults={
            'category': category,
            'brand': brand,
            'price': Decimal(price),
            'stock': stock,
            'description': f'{name} — {"平台自营" if tenant is None else tenant.name}精选商品',
            'gallery': [],
            'status': Product.STATUS_ON_SALE,
            'is_active': True,
        },
    )


def seed_demo_tenants_and_products(
    categories: dict[str, Category],
    brands: dict[str, Brand],
) -> None:
    """Create demo merchants and bind products; keep platform-owned SKUs."""
    now = timezone.now()
    tenants: dict[str, Tenant] = {}

    for item in DEMO_TENANTS:
        tenant, _ = Tenant.objects.update_or_create(
            code=item['code'],
            defaults={
                'name': item['name'],
                'logo': item['logo'],
                'contact_name': item['contact_name'],
                'contact_phone': item['contact_phone'],
                'contact_email': item['contact_email'],
                'address': item['address'],
                'config': item['config'],
                'status': Tenant.STATUS_ACTIVE,
                'is_active': True,
                'approved_at': now,
            },
        )
        tenants[item['code']] = tenant

        for name, category_path, brand_name, price, stock in item['products']:
            category = categories.get(category_path) or categories.get('电子产品')
            brand = brands.get(brand_name) or next(iter(brands.values()))
            _upsert_product(
                name=name,
                category=category,
                brand=brand,
                price=price,
                stock=stock,
                tenant=tenant,
            )

    for name, category_path, brand_name, price, stock in PLATFORM_PRODUCTS:
        category = categories.get(category_path) or categories.get('电子产品')
        brand = brands.get(brand_name) or next(iter(brands.values()))
        _upsert_product(
            name=name,
            category=category,
            brand=brand,
            price=price,
            stock=stock,
            tenant=None,
        )

    seed_demo_seller_staff()


def seed_demo_seller_staff() -> None:
    """Create merchant owner accounts for demo tenants (seller portal login)."""
    User = get_user_model()
    for item in DEMO_TENANTS:
        tenant = Tenant.objects.filter(code=item['code']).first()
        if tenant is None:
            continue
        phone = item['contact_phone']
        user, _ = User.objects.get_or_create(
            username=phone,
            defaults={
                'nickname': item['contact_name'],
                'email': item['contact_email'],
                'phone': phone,
                'is_active': True,
                'is_staff': False,
                'is_superuser': False,
            },
        )
        user.nickname = item['contact_name']
        user.email = item['contact_email']
        user.phone = phone
        user.set_password(DEMO_PASSWORD)
        user.is_active = True
        user.is_staff = False
        user.is_superuser = False
        user.save()
        TenantStaff.objects.update_or_create(
            tenant=tenant,
            user=user,
            defaults={
                'role': TenantStaff.ROLE_OWNER,
                'is_active': True,
            },
        )
