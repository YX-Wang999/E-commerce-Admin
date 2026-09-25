"""Points mall serializers."""

from datetime import timedelta

from django.utils import timezone

from points_mall.models import PointsMallItem, PointsMallOrder


def serialize_item(item: PointsMallItem) -> dict:
    now = timezone.now()
    end_at = item.end_at
    ends_in_seconds = None
    if end_at and end_at > now:
        ends_in_seconds = int((end_at - now).total_seconds())
    is_new = bool(item.created_at and item.created_at >= now - timedelta(days=7))
    return {
        'id': item.id,
        'name': item.name,
        'image': item.image or '',
        'description': item.description or '',
        'item_type': item.item_type,
        'points_required': item.points_required,
        'stock': item.stock,
        'exchanged_count': item.exchanged_count,
        'per_user_limit': item.per_user_limit,
        'requires_address': item.requires_address or item.item_type == PointsMallItem.TYPE_PHYSICAL,
        'is_hot': item.is_hot,
        'is_limited_time': item.is_limited_time,
        'is_new': is_new,
        'start_at': item.start_at.isoformat() if item.start_at else None,
        'end_at': end_at.isoformat() if end_at else None,
        'ends_in_seconds': ends_in_seconds,
        'created_at': item.created_at.isoformat() if item.created_at else None,
        'status': item.status,
    }


def serialize_order(order: PointsMallOrder) -> dict:
    return {
        'id': order.id,
        'order_no': order.order_no,
        'item_id': order.item_id,
        'item_name': order.item_name,
        'item_type': order.item_type,
        'item_image': order.item.image if order.item_id else '',
        'points_spent': order.points_spent,
        'quantity': order.quantity,
        'address': order.address or {},
        'status': order.status,
        'logistics_company': order.logistics_company,
        'logistics_no': order.logistics_no,
        'coupon_code': order.coupon_code,
        'remark': order.remark,
        'shipped_at': order.shipped_at.isoformat() if order.shipped_at else None,
        'created_at': order.created_at.isoformat() if order.created_at else None,
        'customer': {
            'id': order.customer_id,
            'nickname': order.customer.display_name or order.customer.nickname or order.customer.phone,
            'phone': order.customer.phone,
        },
    }
