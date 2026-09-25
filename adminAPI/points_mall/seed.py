"""Points mall demo data and admin menus."""

from datetime import timedelta
from typing import Any

from django.utils import timezone

from points_mall.models import PointsMallItem


DEMO_ITEMS = [
    {
        'name': '保温杯',
        'description': '304不锈钢，保温12小时，适合日常通勤使用。',
        'item_type': PointsMallItem.TYPE_PHYSICAL,
        'points_required': 1200,
        'stock': 43,
        'exchanged_count': 56,
        'per_user_limit': 1,
        'requires_address': True,
        'is_hot': True,
        'is_limited_time': True,
        'end_at': timezone.now() + timedelta(days=14),
        'status': PointsMallItem.STATUS_ON_SALE,
        'sort_order': 10,
    },
    {
        'name': '充电宝',
        'description': '10000mAh 大容量，支持快充。',
        'item_type': PointsMallItem.TYPE_PHYSICAL,
        'points_required': 2000,
        'stock': 30,
        'exchanged_count': 23,
        'per_user_limit': 1,
        'requires_address': True,
        'is_hot': True,
        'status': PointsMallItem.STATUS_ON_SALE,
        'sort_order': 20,
    },
    {
        'name': '满50减10券',
        'description': '全场通用满减券，兑换后可在优惠券中心查看。',
        'item_type': PointsMallItem.TYPE_COUPON,
        'points_required': 500,
        'stock': 999,
        'exchanged_count': 128,
        'per_user_limit': 3,
        'requires_address': False,
        'is_hot': False,
        'status': PointsMallItem.STATUS_ON_SALE,
        'sort_order': 30,
    },
    {
        'name': '包邮卡',
        'description': '单笔订单免运费权益。',
        'item_type': PointsMallItem.TYPE_BENEFIT,
        'points_required': 300,
        'stock': 999,
        'exchanged_count': 89,
        'per_user_limit': 5,
        'requires_address': False,
        'status': PointsMallItem.STATUS_ON_SALE,
        'sort_order': 40,
    },
]


def seed_points_mall_items(item_model: Any = PointsMallItem) -> None:
    for item in DEMO_ITEMS:
        item_model.objects.update_or_create(
            name=item['name'],
            defaults=item,
        )


def seed_points_mall_menus(menu_model: Any, permissions: dict[str, Any]) -> None:
    points_dir = menu_model.objects.filter(name='PointsDir').first()
    if not points_dir:
        return
    menu_defs = [
        ('PointsMallItems', '积分商城商品', '/system/points-mall/items', 'system/points/PointsMallItemsView', 'Present', 101, points_dir, 'points:rule'),
        ('PointsMallOrders', '积分兑换订单', '/system/points-mall/orders', 'system/points/PointsMallOrdersView', 'List', 102, points_dir, 'points:read'),
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
