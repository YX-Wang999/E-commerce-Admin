"""Seed deterministic data for automated tests and local QA."""

from __future__ import annotations

import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.demo_credentials import DEMO_PASSWORD
from customers.models import Customer
from orders.models import Order, OrderItem
from points.models import PointsRule
from products.models import Brand, Category, Product
from promotion.models import Coupon
from rbac.models import Role
from tenants.models import Tenant

User = get_user_model()

ROLE_SPECS = [
    ('super_admin', '超级管理员'),
    ('ops_manager', '运营主管'),
    ('cs_staff', '客服专员'),
]

ORDER_STATUSES = [
    Order.STATUS_PENDING,
    Order.STATUS_PAID,
    Order.STATUS_SHIPPED,
    Order.STATUS_COMPLETED,
    Order.STATUS_CANCELLED,
]


class Command(BaseCommand):
    help = 'Seed test users, products, orders and coupons for QA / E2E'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=10, help='Number of mall customers')
        parser.add_argument('--products', type=int, default=20, help='Number of products')
        parser.add_argument('--orders', type=int, default=30, help='Number of orders')

    @transaction.atomic
    def handle(self, *args, **options):
        user_count = options['users']
        product_count = options['products']
        order_count = options['orders']

        roles = {}
        for code, name in ROLE_SPECS:
            role, _ = Role.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': name, 'is_active': True},
            )
            roles[code] = role

        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@test.local', 'is_staff': True, 'is_superuser': True},
        )
        if not admin.check_password(DEMO_PASSWORD):
            admin.set_password(DEMO_PASSWORD)
            admin.save(update_fields=['password'])
        admin.roles.set([roles['super_admin']])

        for code, _name in ROLE_SPECS[1:]:
            user, created = User.objects.get_or_create(username=code, defaults={'email': f'{code}@test.local'})
            if created or not user.check_password(DEMO_PASSWORD):
                user.set_password(DEMO_PASSWORD)
                user.save(update_fields=['password'])
            user.roles.set([roles[code]])

        tenant, _ = Tenant.objects.get_or_create(
            code='seed-shop',
            defaults={
                'name': '测试旗舰店',
                'contact_name': '测试店主',
                'contact_phone': '13900000001',
                'status': Tenant.STATUS_ACTIVE,
                'is_active': True,
            },
        )

        category, _ = Category.objects.get_or_create(name='测试分类-种子')
        brand, _ = Brand.objects.get_or_create(name='测试品牌-种子')

        products: list[Product] = []
        for index in range(product_count):
            status = Product.STATUS_ON_SALE
            stock = random.randint(5, 100)
            if index % 5 == 0:
                stock = 0
            if index % 7 == 0:
                status = Product.STATUS_OFF_SALE
            product, _ = Product.objects.update_or_create(
                name=f'测试商品-{index + 1:02d}',
                tenant=tenant,
                defaults={
                    'category': category,
                    'brand': brand,
                    'price': Decimal(str(19.9 + index)),
                    'stock': stock,
                    'status': status,
                    'is_active': True,
                },
            )
            products.append(product)

        customers: list[Customer] = []
        for index in range(user_count):
            phone = f'+86138000{index:05d}'
            customer, created = Customer.all_objects.get_or_create(
                phone=phone,
                tenant=None,
                defaults={'nickname': f'测试用户{index + 1}', 'name': f'测试用户{index + 1}'},
            )
            if created:
                customer.set_password(DEMO_PASSWORD)
                customer.save(update_fields=['password'])
            customers.append(customer)

        PointsRule.objects.update_or_create(
            code='sign_in',
            defaults={
                'name': '每日签到',
                'description': '测试签到',
                'rule_type': PointsRule.RULE_EARN,
                'current_value': 10,
                'is_active': True,
            },
        )

        for index in range(order_count):
            customer = random.choice(customers)
            product = random.choice([item for item in products if item.stock > 0] or products)
            status = random.choice(ORDER_STATUSES)
            order = Order.objects.create(
                customer=customer,
                tenant=tenant,
                order_no=f'SEED-{index + 1:05d}',
                total_amount=product.price,
                status=status,
            )
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                unit_price=product.price,
                quantity=1,
            )

        Coupon.objects.get_or_create(
            name='测试满减券',
            tenant=tenant,
            defaults={
                'coupon_type': Coupon.TYPE_FIXED,
                'discount_amount': Decimal('5.00'),
                'min_amount': Decimal('50.00'),
                'total_quantity': 100,
                'per_user_limit': 1,
                'status': Coupon.STATUS_PUBLISHED,
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded staff users, {len(customers)} customers, {len(products)} products, {order_count} orders',
            ),
        )
