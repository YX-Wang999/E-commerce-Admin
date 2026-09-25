"""Ensure demo merchants and seller portal owner accounts exist."""

from django.core.management.base import BaseCommand

from accounts.demo_credentials import DEMO_PASSWORD
from accounts.ecommerce_seed import seed_category_tree
from accounts.tenant_demo_seed import DEMO_TENANTS, seed_demo_seller_staff, seed_demo_tenants_and_products
from products.models import Brand


class Command(BaseCommand):
    help = 'Create demo merchants and seller login accounts (13900000001 / 13900000002)'

    def handle(self, *args, **options) -> None:
        categories = seed_category_tree()
        brands = {}
        for name in ['Apple', '华为', '小米', 'Nike', 'Adidas']:
            brand, _ = Brand.objects.update_or_create(name=name, defaults={'is_active': True})
            brands[name] = brand

        seed_demo_tenants_and_products(categories, brands)
        seed_demo_seller_staff()

        lines = [
            f'商户演示数据已就绪，密码均为 {DEMO_PASSWORD}',
            '',
            '【商户后台 seller.wangyixiang.xyz】账号填手机号：',
        ]
        for item in DEMO_TENANTS:
            lines.append(f'  {item["contact_phone"]}（{item["name"]}）')
        lines.append('')
        lines.append('也可使用店铺名称登录，例如：张三的店')
        self.stdout.write(self.style.SUCCESS('\n'.join(lines)))
