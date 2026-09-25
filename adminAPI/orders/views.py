"""Order views."""

import logging
import uuid
from datetime import datetime, time
from decimal import Decimal

from django.db import transaction
from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from addresses.models import Address
from cart.models import CartItem
from common.pagination import StandardPagination
from common.response import error_response, success_response
from common.tenant import TenantViewSetMixin
from customers.permissions import IsCustomerAuthenticated
from customers.utils import get_request_customer
from orders.export import build_orders_workbook
from orders.models import Order, OrderItem, Refund
from orders.order_no import generate_order_no
from orders.role_filters import apply_order_role_filter, resolve_role_codes
from orders.cancellation import (
    apply_cancel_order_by_customer,
    cancel_pending_order_by_customer,
    process_order_cancellation,
)
from orders.customer_summary import build_customer_order_summary
from orders.receipt import (
    EARLY_RECEIPT_CODE,
    LogisticsNotDeliveredError,
    confirm_order_receipt,
)
from orders.services import (
    get_order_expires_at,
    is_order_expired,
    release_expired_order,
    release_expired_orders,
    resolve_checkout_tenant,
)
from orders.serializers import (
    CustomerCheckoutSerializer,
    CustomerOrderResultSerializer,
    OrderCancelApplySerializer,
    OrderCancelSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    RefundSerializer,
)
from products.inventory import set_inventory_context
from products.models import InventoryLog, Product

logger = logging.getLogger(__name__)


class OrderViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """Order CRUD with ship and export actions."""

    queryset = Order.objects.select_related('customer', 'assigned_to', 'logistics', 'tenant').prefetch_related('items__product', 'cancel_logs').all()
    serializer_class = OrderSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter orders by tenant, role and query params."""
        queryset = super().get_queryset()
        customer = get_request_customer(self.request)
        return self._apply_query_filters(
            queryset,
            customer=customer,
        )

    def _apply_query_filters(self, queryset, customer=None):
        """Apply query params and role-based filters."""
        queryset = apply_order_role_filter(queryset, self.request.user, customer=customer)

        status_param = self.request.query_params.get('status')
        cancel_status = self.request.query_params.get('cancel_status')
        keyword = self.request.query_params.get('keyword')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if status_param == 'canceling':
            queryset = queryset.filter(
                status=Order.STATUS_PAID,
                cancel_status=Order.CANCEL_STATUS_PENDING,
            )
        elif status_param == 'pending_review':
            queryset = queryset.filter(status=Order.STATUS_COMPLETED).annotate(
                review_count=Count('reviews'),
            ).filter(review_count=0)
        elif status_param:
            queryset = queryset.filter(status=status_param)
        if cancel_status:
            queryset = queryset.filter(cancel_status=cancel_status)
        if keyword:
            queryset = queryset.filter(order_no__icontains=keyword)
        if start_date:
            parsed_start = parse_date(start_date)
            if parsed_start:
                start_dt = timezone.make_aware(datetime.combine(parsed_start, time.min))
                queryset = queryset.filter(created_at__gte=start_dt)
        if end_date:
            parsed_end = parse_date(end_date)
            if parsed_end:
                end_dt = timezone.make_aware(datetime.combine(parsed_end, time.max))
                queryset = queryset.filter(created_at__lte=end_dt)
        return queryset

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        """Retrieve order."""
        order = self.get_object()
        customer = get_request_customer(request)
        if customer and order.customer_id != customer.id:
            return error_response('无权查看该订单', http_status=403)
        if customer and is_order_expired(order):
            release_expired_order(order)
            order.refresh_from_db()
        return success_response(data=self.get_serializer(order).data)

    def list(self, request: Request, *args, **kwargs) -> Response:
        """List orders."""
        if get_request_customer(request):
            release_expired_orders()
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create order (admin) or checkout from cart (customer)."""
        items = request.data.get('items') or []
        if items and isinstance(items, list) and isinstance(items[0], dict) and 'cart_item_id' in items[0]:
            return self._create_customer_order(request)
        return self._create_admin_order(request)

    def _create_customer_order(self, request: Request) -> Response:
        """Checkout selected cart items for current mall customer."""
        customer = get_request_customer(request)
        if customer is None:
            return error_response('请先登录', http_status=401)
        serializer = CustomerCheckoutSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))

        address_id = serializer.validated_data['address_id']
        remark = serializer.validated_data.get('remark', '')
        items_data = serializer.validated_data['items']
        coupon_id = serializer.validated_data.get('coupon_id')
        use_points = serializer.validated_data.get('use_points', False)
        points_amount = serializer.validated_data.get('points_amount')
        use_seller_points = serializer.validated_data.get('use_seller_points', False)
        seller_points_amount = serializer.validated_data.get('seller_points_amount')

        try:
            address = Address.objects.get(pk=address_id, customer=customer)
        except Address.DoesNotExist:
            return error_response('收货地址不存在')

        cart_item_ids = [item['cart_item_id'] for item in items_data]
        cart_items = list(
            CartItem.objects.select_related('product', 'cart')
            .filter(id__in=cart_item_ids, cart__customer=customer),
        )
        if len(cart_items) != len(cart_item_ids):
            return error_response('购物车商品不存在或无权操作')

        cart_map = {item.id: item for item in cart_items}

        try:
            with transaction.atomic():
                product_ids = sorted(
                    {cart_map[entry['cart_item_id']].product_id for entry in items_data},
                )
                locked_products = {
                    product.id: product
                    for product in Product.objects.select_for_update().filter(pk__in=product_ids)
                }

                total = Decimal('0')
                line_specs = []

                for entry in items_data:
                    cart_item = cart_map[entry['cart_item_id']]
                    qty = entry['quantity']
                    product = locked_products.get(cart_item.product_id)
                    if product is None:
                        transaction.set_rollback(True)
                        return error_response('商品不存在')
                    if not product.is_active or product.status != Product.STATUS_ON_SALE:
                        transaction.set_rollback(True)
                        return error_response(f'商品「{product.name}」已下架')
                    if qty > cart_item.quantity:
                        transaction.set_rollback(True)
                        return error_response(f'商品「{product.name}」数量超出购物车')
                    if product.stock < qty:
                        transaction.set_rollback(True)
                        return error_response(f'商品「{product.name}」库存不足')
                    line_total = Decimal(str(product.price)) * qty
                    total += line_total
                    line_specs.append((product, qty, product.price, product.name))

                tenant, tenant_error = resolve_checkout_tenant(
                    products=[spec[0] for spec in line_specs],
                    request=request,
                    customer=customer,
                )
                if tenant_error:
                    transaction.set_rollback(True)
                    return error_response(tenant_error)

                original_total = total
                coupon_discount = Decimal('0')
                points_discount = Decimal('0')
                points_used = 0
                seller_points_discount = Decimal('0')
                seller_points_used = 0
                user_coupon = None

                product_qty_pairs = [(spec[0], spec[1]) for spec in line_specs]

                if coupon_id:
                    from promotion.services import validate_user_coupon

                    try:
                        user_coupon, coupon_discount = validate_user_coupon(
                            customer,
                            coupon_id,
                            product_qty_pairs,
                            original_total,
                        )
                    except ValueError as exc:
                        transaction.set_rollback(True)
                        return error_response(str(exc))

                payable = original_total - coupon_discount
                if payable < 0:
                    payable = Decimal('0')

                from points.checkout import validate_points_deduction

                try:
                    points_used, points_discount = validate_points_deduction(
                        customer,
                        payable,
                        use_points,
                        points_amount,
                    )
                except ValueError as exc:
                    transaction.set_rollback(True)
                    return error_response(str(exc))

                payable_after_platform = payable - points_discount
                if payable_after_platform < 0:
                    payable_after_platform = Decimal('0')

                from seller_points.checkout import validate_seller_points_deduction

                try:
                    seller_points_used, seller_points_discount = validate_seller_points_deduction(
                        customer,
                        tenant,
                        payable_after_platform,
                        use_seller_points,
                        seller_points_amount,
                    )
                except ValueError as exc:
                    transaction.set_rollback(True)
                    return error_response(str(exc))

                final_total = payable_after_platform - seller_points_discount
                if final_total < 0:
                    final_total = Decimal('0')

                order = Order.objects.create(
                    order_no=generate_order_no(),
                    customer=customer,
                    tenant=tenant,
                    original_amount=original_total,
                    coupon_discount=coupon_discount,
                    points_discount=points_discount,
                    points_used=points_used,
                    seller_points_discount=seller_points_discount,
                    seller_points_used=seller_points_used,
                    user_coupon=user_coupon,
                    total_amount=final_total,
                    status=Order.STATUS_PENDING,
                    address=f'{address.name} {address.phone} {address.full_address}',
                    remark=remark,
                    expires_at=get_order_expires_at(),
                )
                for product, qty, unit_price, product_name in line_specs:
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=qty,
                        unit_price=unit_price,
                        product_name=product_name,
                    )
                    set_inventory_context(
                        changed_by=None,
                        order=order,
                        change_type=InventoryLog.TYPE_ORDER_DEDUCT,
                        remark=f'下单扣减 {order.order_no}',
                    )
                    product.stock -= qty
                    product.save(update_fields=['stock', 'updated_at'])

                CartItem.objects.filter(id__in=cart_item_ids, cart__customer=customer).delete()

                if user_coupon:
                    from promotion.services import lock_user_coupon

                    lock_user_coupon(user_coupon, order)

                if points_used > 0:
                    from points.checkout import spend_points_for_order

                    spend_points_for_order(customer, order, points_used)

                if seller_points_used > 0:
                    from seller_points.checkout import spend_seller_points_for_order

                    spend_seller_points_for_order(customer, tenant, order, seller_points_used)
        except Exception:
            logger.exception('Customer checkout failed')
            return error_response('订单创建失败', code=50000, http_status=500)

        try:
            from notification.services import notify_new_order

            notify_new_order(order=order)
        except Exception:
            logger.exception('Notify new order failed for order %s', order.id)

        return success_response(
            data=CustomerOrderResultSerializer(order).data,
            message='订单创建成功',
            http_status=status.HTTP_201_CREATED,
        )

    def _create_admin_order(self, request: Request) -> Response:
        """Create order from admin panel."""
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            with transaction.atomic():
                items_data = serializer.validated_data.pop('items')
                total = Decimal('0')
                tenant = getattr(request, 'tenant', None)
                order = Order.objects.create(
                    order_no=f'ORD{uuid.uuid4().hex[:12].upper()}',
                    total_amount=Decimal('0'),
                    status=Order.STATUS_PAID,
                    assigned_to=request.user,
                    tenant=tenant,
                    **serializer.validated_data,
                )
                for item in items_data:
                    product = Product.objects.select_for_update().get(pk=item['product'])
                    qty = item['quantity']
                    if product.stock < qty:
                        return error_response(f'商品「{product.name}」库存不足')
                    line_total = item['unit_price'] * qty
                    total += line_total
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=qty,
                        unit_price=item['unit_price'],
                        product_name=product.name,
                    )
                    set_inventory_context(
                        changed_by=request.user,
                        order=order,
                        change_type=InventoryLog.TYPE_ORDER_DEDUCT,
                        remark=f'订单扣减 {order.order_no}',
                    )
                    product.stock -= qty
                    product.save(update_fields=['stock', 'updated_at'])
                order.total_amount = total
                order.save(update_fields=['total_amount'])
        except Product.DoesNotExist:
            return error_response('商品不存在')
        except Exception:
            logger.exception('Create order failed')
            return error_response('创建订单失败', code=50000, http_status=500)
        try:
            from notification.services import notify_new_order

            notify_new_order(order=order)
        except Exception:
            logger.exception('Notify new order failed for order %s', order.id)
        return success_response(
            data=OrderSerializer(order).data,
            message='创建成功',
            http_status=status.HTTP_201_CREATED,
        )

    def update(self, request: Request, *args, **kwargs) -> Response:
        """Update order."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        allowed = {'address', 'remark', 'logistics_no', 'status'}
        data = {k: v for k, v in request.data.items() if k in allowed}
        old_status = instance.status
        serializer = OrderSerializer(instance, data=data, partial=partial)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Update order failed')
            return error_response('更新失败', code=50000, http_status=500)
        try:
            from notification.services import notify_order_status, notify_pending_shipment

            if old_status != Order.STATUS_PAID and instance.status == Order.STATUS_PAID:
                notify_pending_shipment(order=instance)
            notify_order_status(order=instance, old_status=old_status)
        except Exception:
            logger.exception('Notify order status failed for order %s', instance.id)
        return success_response(data=self.get_serializer(instance).data, message='更新成功')

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Delete order."""
        try:
            self.get_object().delete()
        except Exception:
            logger.exception('Delete order failed')
            return error_response('删除失败', code=50000, http_status=500)
        return success_response(message='删除成功')

    @action(detail=True, methods=['post'], url_path='mock-pay')
    def mock_pay(self, request: Request, pk: int | None = None) -> Response:
        """Simulate payment for a pending customer order."""
        order = self.get_object()
        customer = get_request_customer(request)
        if not customer or order.customer_id != customer.id:
            return error_response('无权操作该订单', http_status=403)
        if order.status != Order.STATUS_PENDING:
            return error_response('当前订单状态不可支付')
        if is_order_expired(order):
            release_expired_order(order)
            return error_response('订单已过期，请重新下单')
        try:
            with transaction.atomic():
                locked = Order.objects.select_for_update().get(pk=order.pk)
                if locked.status != Order.STATUS_PENDING:
                    return error_response('当前订单状态不可支付')
                if is_order_expired(locked):
                    release_expired_order(locked)
                    return error_response('订单已过期，请重新下单')
                locked.status = Order.STATUS_PAID
                locked.paid_at = timezone.now()
                locked.save(update_fields=['status', 'paid_at', 'updated_at'])
                order = locked
        except Exception:
            logger.exception('Mock pay failed for order %s', order.id)
            return error_response('支付失败', code=50000, http_status=500)
        try:
            from notification.services import notify_pending_shipment

            notify_pending_shipment(order=order)
        except Exception:
            logger.exception('Notify pending shipment failed for order %s', order.id)
        return success_response(
            data={
                'id': order.id,
                'status': order.status,
                'paid_at': order.paid_at.isoformat() if order.paid_at else None,
            },
            message='支付成功',
        )

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request: Request, pk: int | None = None) -> Response:
        """Customer direct cancel for pending orders."""
        customer = get_request_customer(request)
        if customer is None:
            return error_response('请先登录', http_status=401)
        order = self.get_object()
        if order.customer_id != customer.id:
            return error_response('无权操作该订单', http_status=403)
        if order.status == Order.STATUS_SHIPPED:
            return error_response('已发货订单不可取消，请拒收或申请退货')
        if order.status != Order.STATUS_PENDING:
            return error_response('当前订单状态不可直接取消')

        serializer = OrderCancelSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            order = cancel_pending_order_by_customer(
                order,
                customer,
                reason=serializer.validated_data['reason'],
                detail=serializer.validated_data.get('detail', ''),
            )
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(data=OrderSerializer(order).data, message='订单已取消')

    @action(detail=True, methods=['post'], url_path='cancel-apply')
    def cancel_apply(self, request: Request, pk: int | None = None) -> Response:
        """Customer apply to cancel a paid (unshipped) order."""
        customer = get_request_customer(request)
        if customer is None:
            return error_response('请先登录', http_status=401)
        order = self.get_object()
        if order.customer_id != customer.id:
            return error_response('无权操作该订单', http_status=403)
        if order.status == Order.STATUS_SHIPPED:
            return error_response('已发货订单不可取消，请拒收或申请退货')
        if order.status != Order.STATUS_PAID:
            return error_response('仅待发货订单可申请取消')

        serializer = OrderCancelApplySerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            order = apply_cancel_order_by_customer(
                order,
                customer,
                reason=serializer.validated_data['reason'],
                detail=serializer.validated_data.get('detail', ''),
            )
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(data=OrderSerializer(order).data, message='取消申请已提交')

    @action(detail=True, methods=['post'], url_path='confirm-receipt')
    def confirm_receipt(self, request: Request, pk: int | None = None) -> Response:
        """Customer confirms order receipt (with early-receipt acknowledgement)."""
        customer = get_request_customer(request)
        if customer is None:
            return error_response('请先登录', http_status=401)
        order = self.get_object()
        if order.customer_id != customer.id:
            return error_response('无权操作该订单', http_status=403)

        early_acknowledged = bool(request.data.get('early_acknowledged'))
        try:
            order, receipt_type = confirm_order_receipt(
                order,
                customer,
                early_acknowledged=early_acknowledged,
            )
        except LogisticsNotDeliveredError:
            return error_response(
                '为了保障您的权益，建议先验货再签收。如您暂不方便当面验收，请录制开箱视频作为后续质保凭证。',
                code=EARLY_RECEIPT_CODE,
                data={'requires_early_ack': True, 'logistics_delivered': False},
            )
        except ValueError as exc:
            return error_response(str(exc))

        if receipt_type == 'early':
            message = (
                '检测到您已确认收货，如货物暂未拿到手，请放心，我们的售后时效以您实际取货之日起计算。'
                '若后续开箱发现异常，请保留照片联系我们。'
            )
        else:
            message = '确认收货成功'
        return success_response(data=OrderSerializer(order).data, message=message)

    @action(detail=True, methods=['post'], url_path='ship')
    def ship(self, request: Request, pk: int | None = None) -> Response:
        """Ship order with express company and tracking number."""
        order = self.get_object()
        express_code = (request.data.get('express_code') or '').strip()
        tracking_number = (
            request.data.get('tracking_number')
            or request.data.get('logistics_no')
            or ''
        ).strip()
        express_company = (request.data.get('express_company') or '').strip()

        if not express_code:
            return error_response('请选择快递公司')
        if not tracking_number:
            return error_response('请填写物流单号')
        if order.status != Order.STATUS_PAID:
            return error_response('当前订单状态不可发货')

        from logistics.express_companies import is_valid_express_code, normalize_express_code
        from logistics.services import create_or_update_logistics_for_ship

        normalized_code = normalize_express_code(express_code)
        if not is_valid_express_code(normalized_code):
            return error_response('不支持的快递公司')

        try:
            with transaction.atomic():
                now = timezone.now()
                order.status = Order.STATUS_SHIPPED
                order.shipped_at = now
                order.save(update_fields=['status', 'shipped_at', 'updated_at'])
                create_or_update_logistics_for_ship(
                    order=order,
                    express_code=normalized_code,
                    tracking_number=tracking_number,
                    express_company=express_company,
                )
                order.refresh_from_db()
        except ValueError as exc:
            return error_response(str(exc))
        except Exception:
            logger.exception('Ship order failed')
            return error_response('发货失败', code=50000, http_status=500)
        try:
            from notification.services import notify_order_status

            notify_order_status(order=order, old_status=Order.STATUS_PAID)
        except Exception:
            logger.exception('Notify shipped failed for order %s', order.id)
        return success_response(data=self.get_serializer(order).data, message='发货成功')

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request: Request) -> HttpResponse:
        """Export orders to Excel with role-based filtering."""
        try:
            queryset = self._apply_query_filters(
                Order.objects.select_related('customer', 'assigned_to').prefetch_related('items__product').all(),
            )
            orders = list(queryset.order_by('-created_at'))
            workbook_buffer = build_orders_workbook(orders)
            filename = f'orders_{timezone.localtime().strftime("%Y%m%d")}.xlsx'
            response = HttpResponse(
                workbook_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception:
            logger.exception('Export orders failed')
            return error_response('导出失败', code=50000, http_status=500)


class RefundViewSet(viewsets.ModelViewSet):
    """Refund CRUD with audit action."""

    queryset = Refund.objects.select_related('order').all()
    serializer_class = RefundSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter refunds."""
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    def list(self, request: Request, *args, **kwargs) -> Response:
        """List refunds."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create refund."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
            order = instance.order
            order.status = Order.STATUS_REFUNDING
            order.save(update_fields=['status', 'updated_at'])
        except Exception:
            logger.exception('Create refund failed')
            return error_response('创建退款申请失败', code=50000, http_status=500)
        try:
            from notification.services import notify_refund_request

            notify_refund_request(refund=instance)
        except Exception:
            logger.exception('Notify refund failed for refund %s', instance.id)
        return success_response(
            data=self.get_serializer(instance).data,
            message='创建成功',
            http_status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request: Request, pk: int | None = None) -> Response:
        """Approve refund."""
        refund = self.get_object()
        if refund.status != Refund.STATUS_PENDING:
            return error_response('该退款申请已处理')
        try:
            with transaction.atomic():
                refund.status = Refund.STATUS_APPROVED
                refund.save(update_fields=['status', 'updated_at'])
                order = refund.order
                from orders.models import CancelLog

                process_order_cancellation(
                    order,
                    cancel_type=Order.CANCEL_TYPE_USER,
                    cancel_reason=refund.reason or '退款审核通过',
                    action=CancelLog.ACTION_MERCHANT_APPROVE,
                    operator_type=CancelLog.OPERATOR_STAFF,
                    operator_id=str(request.user.id),
                    needs_refund=True,
                )
                refund = Refund.objects.select_related('order').get(pk=refund.pk)
        except Exception:
            logger.exception('Approve refund failed')
            return error_response('审核失败', code=50000, http_status=500)
        return success_response(data=self.get_serializer(refund).data, message='退款已通过')

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request: Request, pk: int | None = None) -> Response:
        """Reject refund."""
        refund = self.get_object()
        if refund.status != Refund.STATUS_PENDING:
            return error_response('该退款申请已处理')
        try:
            refund.status = Refund.STATUS_REJECTED
            refund.save(update_fields=['status', 'updated_at'])
        except Exception:
            logger.exception('Reject refund failed')
            return error_response('审核失败', code=50000, http_status=500)
        return success_response(data=self.get_serializer(refund).data, message='退款已拒绝')


class CustomerOrderSummaryView(APIView):
    """Mall profile order badge counts."""

    permission_classes = [IsAuthenticated, IsCustomerAuthenticated]

    def get(self, request: Request) -> Response:
        customer = get_request_customer(request)
        if customer is None:
            return error_response('请先登录', http_status=401)
        return success_response(data=build_customer_order_summary(customer))


class OrderPendingSummaryView(APIView):
    """Count orders awaiting shipment (registered outside router to avoid pk route conflict)."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        queryset = apply_order_role_filter(Order.objects.all(), request.user)
        pending_count = queryset.filter(status=Order.STATUS_PAID).exclude(
            cancel_status=Order.CANCEL_STATUS_PENDING,
        ).count()
        canceling_count = queryset.filter(
            status=Order.STATUS_PAID,
            cancel_status=Order.CANCEL_STATUS_PENDING,
        ).count()
        pending_refund_count = Refund.objects.filter(
            status=Refund.STATUS_PENDING,
            order__in=queryset,
        ).count()
        return success_response(
            data={
                'pending_shipment_count': pending_count,
                'canceling_count': canceling_count,
                'pending_refund_count': pending_refund_count,
            },
        )
