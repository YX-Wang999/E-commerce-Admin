"""Mall customer promotion API views."""

from __future__ import annotations

import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from addresses.models import Address
from cart.models import CartItem
from common.media_utils import file_field_url
from common.response import error_response, success_response
from customers.permissions import IsCustomerAuthenticated
from orders.models import Order, OrderItem
from orders.order_no import generate_order_no
from orders.services import get_order_expires_at, resolve_checkout_tenant
from products.inventory import set_inventory_context
from products.models import InventoryLog, Product
from promotion.models import Coupon, GroupBuyActivity, GroupOrder, SeckillActivity, UserCoupon
from promotion.services import (
    _running_groupbuy_qs,
    _running_seckill_qs,
    groupbuy_progress,
    list_available_coupons,
    receive_coupon,
    seckill_progress,
)

logger = logging.getLogger(__name__)


def _serialize_coupon_template(coupon: Coupon) -> dict:
    return {
        'id': coupon.id,
        'name': coupon.name,
        'coupon_type': coupon.coupon_type,
        'discount_amount': str(coupon.discount_amount or ''),
        'discount_rate': str(coupon.discount_rate or ''),
        'min_amount': str(coupon.min_amount),
        'valid_start': coupon.valid_start.isoformat() if coupon.valid_start else None,
        'valid_end': coupon.valid_end.isoformat() if coupon.valid_end else None,
        'valid_days': coupon.valid_days,
        'status': coupon.status,
    }


def _serialize_user_coupon(uc: UserCoupon) -> dict:
    return {
        'id': uc.id,
        'code': uc.code,
        'status': uc.status,
        'received_at': uc.received_at.isoformat(),
        'expired_at': uc.expired_at.isoformat(),
        'used_at': uc.used_at.isoformat() if uc.used_at else None,
        'coupon': _serialize_coupon_template(uc.coupon),
    }


class MyCouponsView(APIView):
    permission_classes = [IsCustomerAuthenticated]

    def get(self, request: Request) -> Response:
        status_filter = request.query_params.get('status', 'unused')
        qs = UserCoupon.objects.select_related('coupon').filter(customer=request.customer)
        if status_filter == 'unused':
            qs = qs.filter(status=UserCoupon.STATUS_UNUSED, expired_at__gt=timezone.now())
        elif status_filter == 'used':
            qs = qs.filter(status=UserCoupon.STATUS_USED)
        elif status_filter == 'expired':
            qs = qs.filter(
                Q(status=UserCoupon.STATUS_EXPIRED)
                | Q(status=UserCoupon.STATUS_UNUSED, expired_at__lte=timezone.now()),
            )
        data = [_serialize_user_coupon(uc) for uc in qs.order_by('-received_at')[:100]]
        return success_response(data=data)


class AvailableCouponsView(APIView):
    permission_classes = [IsCustomerAuthenticated]

    def get(self, request: Request) -> Response:
        customer = request.customer
        cart_items = list(
            CartItem.objects.select_related('product', 'cart')
            .filter(cart__customer=customer, selected=True),
        )
        if not cart_items:
            cart_items = list(
                CartItem.objects.select_related('product', 'cart').filter(cart__customer=customer),
            )
        products = [(item.product, item.quantity) for item in cart_items]
        subtotal = sum(Decimal(str(item.product.price)) * item.quantity for item in cart_items)
        return success_response(data=list_available_coupons(customer, products, subtotal))


class ReceiveCouponView(APIView):
    permission_classes = [IsCustomerAuthenticated]

    def post(self, request: Request, coupon_id: int) -> Response:
        try:
            uc = receive_coupon(request.customer, coupon_id)
        except Coupon.DoesNotExist:
            return error_response('优惠券不存在', http_status=404)
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(data=_serialize_user_coupon(uc), message='领取成功')


class PublishCouponsView(APIView):
    permission_classes = [IsCustomerAuthenticated]

    def get(self, request: Request) -> Response:
        now = timezone.now()
        qs = Coupon.objects.filter(status=Coupon.STATUS_PUBLISHED).filter(
            Q(valid_type=Coupon.VALID_AFTER_RECEIVE)
            | Q(valid_start__lte=now, valid_end__gte=now),
        )[:50]
        customer = request.customer
        results = []
        for coupon in qs:
            received = UserCoupon.objects.filter(coupon=coupon, customer=customer).count()
            results.append({
                **_serialize_coupon_template(coupon),
                'received_count': received,
                'can_receive': received < coupon.per_user_limit,
            })
        return success_response(data=results)


class SeckillActivitiesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        now = timezone.now()
        activities = (
            SeckillActivity.objects.filter(status=SeckillActivity.STATUS_RUNNING)
            .prefetch_related('products')
            .order_by('-start_time')[:20]
        )
        data = []
        for act in activities:
            product = act.products.first()
            if act.end_time < now:
                phase = 'ended'
            elif act.start_time > now:
                phase = 'upcoming'
            else:
                phase = 'ongoing'
            progress = seckill_progress(act)
            data.append({
                'id': act.id,
                'name': act.name,
                'seckill_price': str(act.seckill_price),
                'seckill_stock': act.seckill_stock,
                'per_user_limit': act.per_user_limit,
                'start_time': act.start_time.isoformat(),
                'end_time': act.end_time.isoformat(),
                'phase': phase,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'price': str(product.price),
                    'image': file_field_url(product.image, product.updated_at.timestamp()),
                } if product else None,
                **progress,
            })
        return success_response(data=data)


class SeckillProductsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        activity_id = request.query_params.get('activity_id')
        now = timezone.now()
        qs = _running_seckill_qs().prefetch_related('products')
        if activity_id:
            qs = qs.filter(pk=activity_id)
        rows = []
        for act in qs[:50]:
            progress = seckill_progress(act)
            for product in act.products.all():
                rows.append({
                    'activity_id': act.id,
                    'activity_name': act.name,
                    'seckill_price': str(act.seckill_price),
                    'seckill_stock': act.seckill_stock,
                    'per_user_limit': act.per_user_limit,
                    'start_time': act.start_time.isoformat(),
                    'end_time': act.end_time.isoformat(),
                    'phase': 'ongoing' if act.start_time <= now <= act.end_time else 'ended',
                    'product_id': product.id,
                    'product_name': product.name,
                    'original_price': str(product.price),
                    'image': file_field_url(product.image, product.updated_at.timestamp()),
                    **progress,
                })
        return success_response(data=rows)


class SeckillBuyView(APIView):
    permission_classes = [IsCustomerAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        customer = request.customer
        address_id = request.data.get('address_id')
        quantity = int(request.data.get('quantity') or 1)
        if quantity < 1:
            return error_response('数量无效')

        try:
            activity = _running_seckill_qs().prefetch_related('products').get(pk=pk)
        except SeckillActivity.DoesNotExist:
            return error_response('秒杀活动不存在或已结束', http_status=404)

        try:
            address = Address.objects.get(pk=address_id, customer=customer)
        except Address.DoesNotExist:
            return error_response('收货地址不存在')

        product = activity.products.first()
        if product is None:
            return error_response('秒杀商品不存在')

        bought = OrderItem.objects.filter(
            order__customer=customer,
            order__promotion_ref=str(activity.id),
            order__promotion_type='seckill',
        ).exclude(order__status=Order.STATUS_CANCELLED).aggregate(total=Sum('quantity'))['total'] or 0

        if bought + quantity > activity.per_user_limit:
            return error_response(f'每人限购 {activity.per_user_limit} 件')

        try:
            with transaction.atomic():
                activity = SeckillActivity.objects.select_for_update().get(pk=activity.pk)
                product = Product.objects.select_for_update().get(pk=product.pk)
                if activity.seckill_stock < quantity:
                    return error_response('秒杀库存不足')
                if product.stock < quantity:
                    return error_response('商品库存不足')

                unit_price = activity.seckill_price
                total = Decimal(str(unit_price)) * quantity
                tenant, tenant_error = resolve_checkout_tenant(
                    products=[product],
                    request=request,
                    customer=customer,
                )
                if tenant_error:
                    return error_response(tenant_error)

                order = Order.objects.create(
                    order_no=generate_order_no(),
                    customer=customer,
                    tenant=tenant,
                    original_amount=Decimal(str(product.price)) * quantity,
                    total_amount=total,
                    status=Order.STATUS_PENDING,
                    address=f'{address.name} {address.phone} {address.full_address}',
                    remark=str(request.data.get('remark') or ''),
                    expires_at=get_order_expires_at(),
                    promotion_type='seckill',
                    promotion_ref=str(activity.id),
                )
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    product_name=product.name,
                )
                activity.seckill_stock -= quantity
                activity.save(update_fields=['seckill_stock', 'updated_at'])
                set_inventory_context(
                    changed_by=None,
                    order=order,
                    change_type=InventoryLog.TYPE_ORDER_DEDUCT,
                    remark=f'秒杀下单 {order.order_no}',
                )
                product.stock -= quantity
                product.save(update_fields=['stock', 'updated_at'])
        except Exception:
            logger.exception('Seckill buy failed')
            return error_response('秒杀下单失败', code=50000, http_status=500)

        return success_response(
            data={'id': order.id, 'order_no': order.order_no, 'total_amount': str(order.total_amount)},
            message='秒杀订单创建成功',
        )


class GroupBuyActivitiesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        product_id = request.query_params.get('product_id')
        qs = _running_groupbuy_qs().select_related('product')
        if product_id:
            qs = qs.filter(product_id=product_id)
        data = []
        for act in qs[:20]:
            progress = groupbuy_progress(act)
            data.append({
                'id': act.id,
                'name': act.name,
                'group_price': str(act.group_price),
                'group_size': act.group_size,
                'stock': act.stock,
                'end_time': act.end_time.isoformat(),
                'product': {
                    'id': act.product_id,
                    'name': act.product.name,
                    'price': str(act.product.price),
                    'image': file_field_url(act.product.image, act.product.updated_at.timestamp()),
                },
                **progress,
            })
        return success_response(data=data)


class GroupBuyJoinView(APIView):
    permission_classes = [IsCustomerAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        customer = request.customer
        address_id = request.data.get('address_id')
        group_order_id = request.data.get('group_order_id')
        quantity = int(request.data.get('quantity') or 1)

        try:
            activity = _running_groupbuy_qs().select_related('product').get(pk=pk)
        except GroupBuyActivity.DoesNotExist:
            return error_response('团购活动不存在或已结束', http_status=404)

        try:
            address = Address.objects.get(pk=address_id, customer=customer)
        except Address.DoesNotExist:
            return error_response('收货地址不存在')

        product = activity.product
        group_order = None
        try:
            with transaction.atomic():
                activity = GroupBuyActivity.objects.select_for_update().get(pk=activity.pk)
                product = Product.objects.select_for_update().get(pk=product.pk)
                if activity.stock < quantity:
                    return error_response('团购库存不足')
                if product.stock < quantity:
                    return error_response('商品库存不足')

                unit_price = activity.group_price
                total = Decimal(str(unit_price)) * quantity
                tenant, tenant_error = resolve_checkout_tenant(
                    products=[product],
                    request=request,
                    customer=customer,
                )
                if tenant_error:
                    return error_response(tenant_error)

                order = Order.objects.create(
                    order_no=generate_order_no(),
                    customer=customer,
                    tenant=tenant,
                    original_amount=Decimal(str(product.price)) * quantity,
                    total_amount=total,
                    status=Order.STATUS_PENDING,
                    address=f'{address.name} {address.phone} {address.full_address}',
                    remark=str(request.data.get('remark') or ''),
                    expires_at=get_order_expires_at(),
                    promotion_type='groupbuy',
                    promotion_ref=str(activity.id),
                )
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    product_name=product.name,
                )
                activity.stock -= quantity
                activity.save(update_fields=['stock', 'updated_at'])
                set_inventory_context(
                    changed_by=None,
                    order=order,
                    change_type=InventoryLog.TYPE_ORDER_DEDUCT,
                    remark=f'团购下单 {order.order_no}',
                )
                product.stock -= quantity
                product.save(update_fields=['stock', 'updated_at'])

                if group_order_id:
                    group_order = GroupOrder.objects.select_for_update().get(
                        pk=group_order_id,
                        activity=activity,
                        status=GroupOrder.STATUS_PENDING,
                    )
                    pending_count = GroupOrder.objects.filter(
                        activity=activity,
                        status=GroupOrder.STATUS_PENDING,
                    ).count()
                    if pending_count + 1 >= activity.group_size:
                        GroupOrder.objects.filter(
                            activity=activity,
                            status=GroupOrder.STATUS_PENDING,
                        ).update(status=GroupOrder.STATUS_SUCCESS)
                else:
                    expired_at = timezone.now() + timezone.timedelta(hours=activity.group_valid_hours)
                    group_order = GroupOrder.objects.create(
                        activity=activity,
                        order=order,
                        status=GroupOrder.STATUS_PENDING,
                        expired_at=expired_at,
                    )
        except GroupOrder.DoesNotExist:
            return error_response('拼团不存在或已结束')
        except Exception:
            logger.exception('Groupbuy join failed')
            return error_response('团购下单失败', code=50000, http_status=500)

        return success_response(
            data={
                'id': order.id,
                'order_no': order.order_no,
                'group_order_id': group_order.id if group_order else None,
                'total_amount': str(order.total_amount),
            },
            message='团购订单创建成功',
        )
