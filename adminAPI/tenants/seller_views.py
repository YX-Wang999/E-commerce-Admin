"""Seller portal API views."""

import logging
import re

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from datetime import timedelta
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from chat.models import Conversation, Message
from chat.serializers import MessageSerializer
from chat.services import create_chat_message, open_tenant_platform_conversation
from common.response import error_response, status_blocked_response, success_response
from customers.models import Customer
from orders.cancellation import (
    cancel_order_by_merchant,
    review_cancel_apply_by_merchant,
)
from orders.models import Order
from products.models import Brand, Category, Product
from products.serializers import CategorySerializer, ProductSerializer
from orders.serializers import OrderCancelReviewSerializer, OrderCancelSerializer, OrderSerializer
from customers.serializers import CustomerSerializer
from tenants.models import Tenant, TenantAppeal, TenantAppealMessage, TenantInboxMessage, TenantStaff
from tenants.seller_permissions import IsTenantStaffManager, IsTenantStaffMember
from tenants.seller_serializers import SellerLoginSerializer, verify_seller_credentials
from tenants.serializers import (
    SellerAppealDetailSerializer,
    SellerTenantProfileUpdateSerializer,
    TenantInboxMessageSerializer,
    TenantSerializer,
    TenantStaffSerializer,
)
from tenants.change_services import submit_tenant_profile_changes
from tenants.services import build_tenant_login_block
from tenants.validators import check_tenant_availability
from tenants.utils import resolve_or_reuse_seller_user

logger = logging.getLogger(__name__)
User = get_user_model()
PHONE_PATTERN = re.compile(r'^1[3-9]\d{9}$')

APPEAL_ELIGIBLE_STATUSES = {Tenant.STATUS_SUSPENDED, Tenant.STATUS_CLOSED, Tenant.STATUS_PENDING}


def _issue_seller_tokens(user: User) -> tuple[str, str]:
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def _verify_appeal_credentials(account: str, password: str):
    user, tenant, staff = verify_seller_credentials(account, password)
    if tenant is None:
        return None, None, None, error_response('商户不存在，请检查名称或手机号')
    if user is None or staff is None:
        return None, None, None, error_response('账号或密码错误')
    if tenant.status not in APPEAL_ELIGIBLE_STATUSES:
        return None, None, None, error_response('当前账户状态无需申诉，请直接登录')
    return user, tenant, staff, None


def _notify_platform_appeal(tenant: Tenant, appeal: TenantAppeal) -> Conversation:
    conversation = open_tenant_platform_conversation(tenant)
    Message.objects.create(
        conversation=conversation,
        sender_type=Message.SENDER_SYSTEM,
        content=(
            f'【商户申诉 #{appeal.id}】{tenant.name}\n'
            f'标题：{appeal.title}\n'
            f'{appeal.content[:800]}'
        ),
    )
    conversation.unread_count_staff = (conversation.unread_count_staff or 0) + 1
    conversation.save(update_fields=['unread_count_staff', 'updated_at'])
    from tenants.notify import push_admin_alert

    push_admin_alert(
        {
            'type': 'system_alert',
            'level': 'urgent',
            'title': f'【新申诉】{tenant.name}',
            'content': f'{appeal.title}：{appeal.content[:120]}',
            'target_url': '/tenants/appeals',
            'appeal_id': appeal.id,
            'tenant_id': tenant.id,
        },
    )
    return conversation


SELLER_MENUS = [
    {'path': '/', 'icon': 'Odometer', 'label': '仪表盘'},
    {'path': '/products', 'icon': 'Goods', 'label': '商品管理'},
    {'path': '/orders', 'icon': 'List', 'label': '订单管理'},
    {'path': '/customers', 'icon': 'User', 'label': '客户管理'},
    {'path': '/chat', 'icon': 'ChatDotRound', 'label': '在线客服'},
    {'path': '/settings', 'icon': 'Setting', 'label': '店铺设置'},
    {'path': '/staff', 'icon': 'UserFilled', 'label': '员工管理'},
]


def _get_tenant_order(tenant: Tenant, pk: int) -> Order | None:
    return (
        Order.all_objects.filter(tenant=tenant, pk=pk)
        .select_related('customer', 'logistics')
        .prefetch_related('items', 'cancel_logs')
        .first()
    )


def _get_tenant_product(tenant: Tenant, pk: int) -> Product | None:
    return Product.all_objects.filter(tenant=tenant, pk=pk).select_related('category', 'brand').first()


class SellerLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = SellerLoginSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message), code=40002)

        tenant = serializer.validated_data['tenant']
        blocked = build_tenant_login_block(tenant)
        if blocked is not None:
            return status_blocked_response(blocked['message'], data=blocked['data'])

        user = serializer.validated_data['user']
        staff = serializer.validated_data['staff']
        refresh = RefreshToken.for_user(user)
        return success_response(
            data={
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'nickname': user.nickname or user.username,
                    'email': user.email,
                },
                'tenant': TenantSerializer(tenant).data,
                'staff_role': staff.role,
                'menus': SELLER_MENUS,
            },
            message='登录成功',
        )


class SellerProfileView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        tenant = request.tenant
        staff = request.user.tenant_staffs.filter(tenant=tenant, is_active=True).first()
        if staff is None:
            return error_response('员工信息不存在', http_status=403)
        return success_response(
            data={
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'nickname': request.user.nickname or request.user.username,
                    'email': request.user.email,
                },
                'tenant': TenantSerializer(tenant).data,
                'staff_role': staff.role,
                'menus': SELLER_MENUS,
            },
        )


class SellerTenantProfileView(APIView):
    """Update tenant profile with change review workflow."""

    permission_classes = [IsAuthenticated, IsTenantStaffManager]

    def put(self, request: Request) -> Response:
        tenant = request.tenant
        serializer = SellerTenantProfileUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message))
        payload = {
            key: value
            for key, value in serializer.validated_data.items()
            if value is not None and (value != '' or key == 'config')
        }
        if not payload:
            return error_response('没有可更新的字段')
        result = submit_tenant_profile_changes(tenant=tenant, user=request.user, payload=payload)
        if not result['ok']:
            first_error = next(iter(result['errors'].values()))
            return error_response(first_error)
        tenant.refresh_from_db()
        message_parts = []
        if result['direct_updated']:
            message_parts.append('保存成功')
        if result['pending_submitted']:
            message_parts.append('部分修改已提交，等待平台审核')
        return success_response(
            data={
                'tenant': TenantSerializer(tenant).data,
                'direct_updated': result['direct_updated'],
                'pending_submitted': result['pending_submitted'],
            },
            message='；'.join(message_parts) or '保存成功',
        )


class SellerTenantCloseView(APIView):
    """Deprecated: direct close replaced by closure application workflow."""

    permission_classes = [IsAuthenticated, IsTenantStaffManager]

    def post(self, request: Request) -> Response:
        return error_response('请通过「店铺注销」提交申请，平台审核并公示后方可正式注销')


def _format_money(value) -> str:
    from decimal import Decimal

    amount = Decimal(str(value or 0))
    return f'{amount.quantize(Decimal("0.01")):.2f}'


class SellerDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        from tenants.dashboard_stats import compute_seller_dashboard_stats, format_money

        tenant = request.tenant
        today = timezone.localdate()
        start_date = today - timedelta(days=6)
        paid_statuses = [Order.STATUS_PAID, Order.STATUS_SHIPPED, Order.STATUS_COMPLETED]
        order_qs = Order.all_objects.filter(tenant=tenant)
        product_qs = Product.all_objects.filter(tenant=tenant, is_active=True)
        core_stats = compute_seller_dashboard_stats(tenant)

        product_count = product_qs.count()
        conversation_count = Conversation.all_objects.filter(tenant=tenant).count()
        pending_orders = order_qs.filter(status=Order.STATUS_PENDING).count()
        low_stock_count = product_qs.filter(stock__lte=10).count()

        sales_rows = (
            order_qs.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=today,
                status__in=paid_statuses,
            )
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(amount=Sum('total_amount'), orders=Count('id'))
            .order_by('day')
        )
        sales_map = {row['day']: row for row in sales_rows}
        sales_trend = []
        for offset in range(7):
            day = start_date + timedelta(days=offset)
            row = sales_map.get(day)
            sales_trend.append(
                {
                    'date': day.isoformat(),
                    'amount': format_money(row['amount']) if row and row['amount'] is not None else '0.00',
                    'orders': row['orders'] if row else 0,
                },
            )

        recent_orders = OrderSerializer(
            order_qs.select_related('customer').prefetch_related('items').order_by('-id')[:5],
            many=True,
        ).data
        low_stock_products = ProductSerializer(
            product_qs.filter(stock__lte=10).order_by('stock', '-id')[:10],
            many=True,
        ).data

        return success_response(
            data={
                'product_count': product_count,
                'order_count': core_stats['order_count'],
                'customer_count': core_stats['customer_count'],
                'conversation_count': conversation_count,
                'pending_orders': pending_orders,
                'paid_orders': core_stats['paid_orders'],
                'today_orders': core_stats['today_orders'],
                'today_sales': core_stats['today_sales'],
                'total_revenue': core_stats['total_revenue'],
                'cancelled_orders': core_stats['cancelled_orders'],
                'low_stock': low_stock_count,
                'sales_trend': sales_trend,
                'recent_orders': recent_orders,
                'low_stock_products': low_stock_products,
            },
        )


class SellerProductListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        from common.pagination import StandardPagination

        queryset = Product.all_objects.filter(tenant=request.tenant).select_related('category', 'brand')
        keyword = (request.query_params.get('keyword') or '').strip()
        status_param = (request.query_params.get('status') or '').strip()
        if keyword:
            queryset = queryset.filter(name__icontains=keyword)
        if status_param:
            queryset = queryset.filter(status=status_param)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset.order_by('-id'), request)
        serializer = ProductSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = ProductSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message))
        product = serializer.save(tenant=request.tenant)
        return success_response(data=ProductSerializer(product).data, message='商品已创建')


class SellerOrderListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        from common.pagination import StandardPagination

        queryset = Order.all_objects.filter(tenant=request.tenant).select_related('customer')
        status_param = (request.query_params.get('status') or '').strip()
        keyword = (request.query_params.get('keyword') or '').strip()
        if status_param == 'canceling':
            queryset = queryset.filter(
                status=Order.STATUS_PAID,
                cancel_status=Order.CANCEL_STATUS_PENDING,
            )
        elif status_param:
            queryset = queryset.filter(status=status_param)
        if keyword:
            queryset = queryset.filter(
                Q(order_no__icontains=keyword) | Q(customer__phone__icontains=keyword),
            )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset.order_by('-id'), request)
        serializer = OrderSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class SellerOrderDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request, pk: int) -> Response:
        order = _get_tenant_order(request.tenant, pk)
        if order is None:
            return error_response('订单不存在', http_status=404)
        return success_response(data=OrderSerializer(order).data)


class SellerOrderShipView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def post(self, request: Request, pk: int) -> Response:
        order = _get_tenant_order(request.tenant, pk)
        if order is None:
            return error_response('订单不存在', http_status=404)

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
            logger.exception('Seller ship order failed')
            return error_response('发货失败', code=50000, http_status=500)

        try:
            from notification.services import notify_order_status

            notify_order_status(order=order, old_status=Order.STATUS_PAID)
        except Exception:
            logger.exception('Notify shipped failed for order %s', order.id)

        order = _get_tenant_order(request.tenant, pk)
        return success_response(data=OrderSerializer(order).data, message='发货成功')


class SellerOrderCancelReviewView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def post(self, request: Request, pk: int) -> Response:
        order = _get_tenant_order(request.tenant, pk)
        if order is None:
            return error_response('订单不存在', http_status=404)

        serializer = OrderCancelReviewSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message))

        try:
            order = review_cancel_apply_by_merchant(
                order,
                approve=serializer.validated_data['approve'],
                remark=serializer.validated_data.get('remark', ''),
                operator_id=str(request.user.id),
            )
        except ValueError as exc:
            return error_response(str(exc))
        except Exception:
            logger.exception('Seller cancel review failed')
            return error_response('审核失败', code=50000, http_status=500)

        order = _get_tenant_order(request.tenant, pk)
        message = '已同意取消' if serializer.validated_data['approve'] else '已驳回取消申请'
        return success_response(data=OrderSerializer(order).data, message=message)


class SellerOrderCancelView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def post(self, request: Request, pk: int) -> Response:
        order = _get_tenant_order(request.tenant, pk)
        if order is None:
            return error_response('订单不存在', http_status=404)

        serializer = OrderCancelSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message))

        try:
            order = cancel_order_by_merchant(
                order,
                reason=serializer.validated_data['reason'],
                operator_id=str(request.user.id),
            )
        except ValueError as exc:
            return error_response(str(exc))
        except Exception:
            logger.exception('Seller cancel order failed')
            return error_response('取消失败', code=50000, http_status=500)

        order = _get_tenant_order(request.tenant, pk)
        return success_response(data=OrderSerializer(order).data, message='订单已取消')


class SellerProductDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request, pk: int) -> Response:
        product = _get_tenant_product(request.tenant, pk)
        if product is None:
            return error_response('商品不存在', http_status=404)
        return success_response(data=ProductSerializer(product).data)

    def put(self, request: Request, pk: int) -> Response:
        product = _get_tenant_product(request.tenant, pk)
        if product is None:
            return error_response('商品不存在', http_status=404)
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message))
        product = serializer.save()
        return success_response(data=ProductSerializer(product).data, message='商品已更新')


class SellerProductToggleView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def patch(self, request: Request, pk: int) -> Response:
        product = _get_tenant_product(request.tenant, pk)
        if product is None:
            return error_response('商品不存在', http_status=404)
        target_status = (request.data.get('status') or '').strip()
        if target_status in {Product.STATUS_ON_SALE, Product.STATUS_OFF_SALE}:
            product.status = target_status
        elif product.status == Product.STATUS_ON_SALE:
            product.status = Product.STATUS_OFF_SALE
        else:
            product.status = Product.STATUS_ON_SALE
        product.save(update_fields=['status', 'updated_at'])
        return success_response(data=ProductSerializer(product).data, message='状态已更新')


class SellerCategoryListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        queryset = Category.objects.filter(is_active=True).order_by('sort_order', 'id')
        return success_response(data=CategorySerializer(queryset, many=True).data)


class SellerBrandListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        queryset = Brand.objects.filter(is_active=True).order_by('name')
        data = [{'id': item.id, 'name': item.name} for item in queryset]
        return success_response(data=data)


class SellerExpressCompaniesView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        from logistics.express_companies import EXPRESS_COMPANIES

        return success_response(data=EXPRESS_COMPANIES)


class SellerCustomerDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request, pk: int) -> Response:
        customer = Customer.all_objects.filter(pk=pk).first()
        if customer is None:
            return error_response('客户不存在', http_status=404)
        has_order = Order.all_objects.filter(tenant=request.tenant, customer=customer).exists()
        if not has_order:
            return error_response('客户不存在', http_status=404)
        orders = (
            Order.all_objects.filter(tenant=request.tenant, customer=customer)
            .select_related('customer')
            .prefetch_related('items')
            .order_by('-id')[:20]
        )
        return success_response(
            data={
                'customer': CustomerSerializer(customer).data,
                'orders': OrderSerializer(orders, many=True).data,
            },
        )


class SellerCustomerListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        from common.pagination import StandardPagination
        from django.db.models import Subquery

        tenant = request.tenant
        order_customer_ids = Order.all_objects.filter(tenant=tenant).values('customer_id')
        queryset = Customer.all_objects.filter(id__in=Subquery(order_customer_ids))
        keyword = (request.query_params.get('keyword') or '').strip()
        if keyword:
            queryset = queryset.filter(
                Q(name__icontains=keyword) | Q(phone__icontains=keyword) | Q(nickname__icontains=keyword),
            )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset.order_by('-id'), request)
        rows = []
        for customer in page:
            order_count = Order.all_objects.filter(tenant=tenant, customer=customer).count()
            rows.append(
                {
                    'id': customer.id,
                    'phone': customer.phone,
                    'email': customer.email or '',
                    'nickname': customer.nickname or '',
                    'name': customer.name or '',
                    'display_name': customer.display_name,
                    'avatar': customer.avatar or '',
                    'level': customer.level,
                    'points': customer.points,
                    'is_active': customer.is_active,
                    'registered_at': customer.registered_at,
                    'created_at': customer.created_at,
                    'updated_at': customer.updated_at,
                    'order_count': order_count,
                },
            )
        return paginator.get_paginated_response(rows)


class SellerStaffListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        queryset = TenantStaff.objects.filter(tenant=request.tenant).select_related('user', 'tenant')
        serializer = TenantStaffSerializer(queryset, many=True)
        return success_response(data=serializer.data)


class SellerStaffCreateView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffManager]

    def post(self, request: Request) -> Response:
        user_id = request.data.get('user')
        role = request.data.get('role', TenantStaff.ROLE_STAFF)
        if not user_id:
            return error_response('请选择用户')
        if role not in {TenantStaff.ROLE_OWNER, TenantStaff.ROLE_MANAGER, TenantStaff.ROLE_STAFF}:
            return error_response('无效的角色')
        user = User.objects.filter(pk=user_id, is_active=True).first()
        if user is None:
            return error_response('用户不存在')
        staff, created = TenantStaff.objects.get_or_create(
            tenant=request.tenant,
            user=user,
            defaults={'role': role, 'is_active': True},
        )
        if not created:
            staff.role = role
            staff.is_active = True
            staff.save(update_fields=['role', 'is_active'])
        return success_response(
            data=TenantStaffSerializer(staff).data,
            message='员工已添加',
        )


class SellerStaffDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffManager]

    def delete(self, request: Request, pk: int) -> Response:
        staff = TenantStaff.objects.filter(tenant=request.tenant, pk=pk).first()
        if staff is None:
            return error_response('员工不存在', code=40404, http_status=404)
        if staff.role == TenantStaff.ROLE_OWNER:
            return error_response('不能删除店主账号')
        staff.delete()
        return success_response(message='已移除员工')


class SellerTenantApplyCheckView(APIView):
    """Public field availability check for seller onboarding."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        field = (request.data.get('field') or '').strip()
        value = request.data.get('value')
        kwargs = {}
        if field == 'name':
            kwargs['name'] = value
        elif field == 'contact_name':
            kwargs['contact_name'] = value
        elif field == 'contact_phone':
            kwargs['phone'] = value
            kwargs['for_apply'] = True
        else:
            return error_response('不支持的校验字段')
        return success_response(data=check_tenant_availability(**kwargs))


class SellerTenantApplyView(APIView):
    """Public tenant onboarding application."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        required = ['name', 'contact_name', 'contact_phone', 'contact_email', 'password']
        for field in required:
            if not str(request.data.get(field, '')).strip():
                return error_response(f'请填写{field}')
        password = str(request.data.get('password', '')).strip()
        if len(password) < 8:
            return error_response('密码至少 8 位')
        phone = str(request.data['contact_phone']).strip()
        if not PHONE_PATTERN.match(phone):
            return error_response('请输入正确的手机号')
        name = str(request.data['name']).strip()
        contact_name = str(request.data['contact_name']).strip()
        from tenants.name_rules import validate_tenant_name

        name_error = validate_tenant_name(name)
        if name_error:
            return error_response(name_error)
        availability = check_tenant_availability(
            phone=phone,
            name=name,
            contact_name=contact_name,
            for_apply=True,
        )
        if not availability['available']:
            return error_response(availability['errors'][0])
        try:
            user = resolve_or_reuse_seller_user(
                phone=phone,
                password=password,
                contact_name=contact_name,
                email=str(request.data['contact_email']).strip(),
            )
        except ValueError as exc:
            return error_response(str(exc))
        try:
            tenant = Tenant.objects.create(
                name=name,
                contact_name=contact_name,
                contact_phone=phone,
                contact_email=request.data['contact_email'].strip(),
                address=(request.data.get('address') or '').strip(),
                status=Tenant.STATUS_PENDING,
            )
            TenantStaff.objects.create(
                tenant=tenant,
                user=user,
                role=TenantStaff.ROLE_OWNER,
                is_active=False,
            )
        except IntegrityError:
            return error_response('该联系电话已被其他商户使用')
        try:
            from notification.services import notify_tenant_apply

            notify_tenant_apply(tenant=tenant)
        except Exception:
            logger.exception('Notify tenant apply failed for tenant %s', tenant.id)
        return success_response(
            data=TenantSerializer(tenant).data,
            message='入驻申请已提交，当前为待审核状态，审核通过后可登录',
        )


class SellerAppealCreateView(APIView):
    """Submit tenant appeal without login (verify account/password)."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        account = str(request.data.get('account', '')).strip()
        password = str(request.data.get('password', ''))
        title = str(request.data.get('title', '')).strip()
        content = str(request.data.get('content', '')).strip()
        attachments = request.data.get('attachments') or []

        if not account or not password:
            return error_response('请先填写登录账号和密码以验证身份')
        if not title:
            return error_response('请填写申诉标题')
        if not content:
            return error_response('请填写申诉内容')
        if not isinstance(attachments, list):
            attachments = []

        user, tenant, staff, error = _verify_appeal_credentials(account, password)
        if error is not None:
            return error

        pending_count = TenantAppeal.objects.filter(
            tenant=tenant,
            status__in=[TenantAppeal.STATUS_PENDING, TenantAppeal.STATUS_PROCESSING],
        ).count()
        if pending_count >= 3:
            return error_response('您有申诉正在处理中，请耐心等待平台回复')

        appeal = TenantAppeal.objects.create(
            tenant=tenant,
            title=title,
            content=content,
            attachments=attachments[:3],
        )
        TenantAppealMessage.objects.create(
            appeal=appeal,
            sender_type=TenantAppealMessage.SENDER_MERCHANT,
            sender_user=user,
            content=content,
        )
        conversation = _notify_platform_appeal(tenant, appeal)
        access, refresh = _issue_seller_tokens(user)
        return success_response(
            data={
                'id': appeal.id,
                'status': appeal.status,
                'conversation_id': conversation.id,
                'user_id': user.id,
                'access': access,
                'refresh': refresh,
            },
            message='申诉已提交，已为您连接平台客服',
        )


class SellerAppealChatOpenView(APIView):
    """Open B2P platform chat for blocked seller (verify account/password)."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        account = str(request.data.get('account', '')).strip()
        password = str(request.data.get('password', ''))
        if not account or not password:
            return error_response('请先填写登录账号和密码以验证身份')

        user, tenant, _staff, error = _verify_appeal_credentials(account, password)
        if error is not None:
            return error

        conversation = open_tenant_platform_conversation(tenant)
        access, refresh = _issue_seller_tokens(user)
        return success_response(
            data={
                'conversation_id': conversation.id,
                'tenant_name': tenant.name,
                'user_id': user.id,
                'access': access,
                'refresh': refresh,
            },
            message='已连接平台客服',
        )


class SellerAppealChatMessageView(APIView):
    """List or send messages in appeal B2P chat without full login."""

    permission_classes = [AllowAny]

    def _resolve_conversation(self, request: Request):
        if request.method == 'GET':
            account = str(request.query_params.get('account', '')).strip()
            password = str(request.query_params.get('password', ''))
            conversation_id = request.query_params.get('conversation_id')
        else:
            account = str(request.data.get('account', '')).strip()
            password = str(request.data.get('password', ''))
            conversation_id = request.data.get('conversation_id')

        if not account or not password:
            return None, None, None, error_response('请先填写登录账号和密码以验证身份')
        if not conversation_id:
            return None, None, None, error_response('缺少会话 ID')

        user, tenant, _staff, error = _verify_appeal_credentials(account, password)
        if error is not None:
            return None, None, None, error

        try:
            conversation_id = int(conversation_id)
        except (TypeError, ValueError):
            return None, None, None, error_response('无效的会话 ID')

        conversation = Conversation.all_objects.filter(
            pk=conversation_id,
            tenant=tenant,
            conversation_type=Conversation.TYPE_B2P,
        ).first()
        if conversation is None:
            return None, None, None, error_response('会话不存在或无权访问')
        return user, tenant, conversation, None

    def get(self, request: Request) -> Response:
        _user, _tenant, conversation, error = self._resolve_conversation(request)
        if error is not None:
            return error
        messages = conversation.messages.select_related('sender_staff', 'sender_user').order_by('created_at')
        return success_response(data=MessageSerializer(messages, many=True).data)

    def post(self, request: Request) -> Response:
        user, _tenant, conversation, error = self._resolve_conversation(request)
        if error is not None:
            return error
        content = str(request.data.get('content', '')).strip()
        if not content:
            return error_response('消息内容不能为空')
        try:
            message = create_chat_message(
                conversation,
                content,
                is_staff=True,
                staff_user=user,
            )
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(
            data=MessageSerializer(message).data,
            message='发送成功',
        )


class SellerInboxSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        tenant = request.tenant
        unread_qs = TenantInboxMessage.objects.filter(tenant=tenant, is_read=False)
        latest = unread_qs.filter(message_type=TenantInboxMessage.TYPE_APPEAL_REPLY).first()
        return success_response(
            data={
                'unread_count': unread_qs.count(),
                'latest_appeal_reply': TenantInboxMessageSerializer(latest).data if latest else None,
            },
        )


class SellerInboxListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        tenant = request.tenant
        queryset = TenantInboxMessage.objects.filter(tenant=tenant).order_by('-created_at')[:50]
        return success_response(data=TenantInboxMessageSerializer(queryset, many=True).data)


class SellerInboxReadView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def post(self, request: Request, pk: int) -> Response:
        tenant = request.tenant
        message = TenantInboxMessage.objects.filter(tenant=tenant, pk=pk).first()
        if message is None:
            return error_response('消息不存在', http_status=404)
        if not message.is_read:
            message.is_read = True
            message.save(update_fields=['is_read'])
        return success_response(message='已标记为已读')


class SellerInboxReadAllView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def post(self, request: Request) -> Response:
        tenant = request.tenant
        updated = TenantInboxMessage.objects.filter(tenant=tenant, is_read=False).update(is_read=True)
        return success_response(data={'updated': updated}, message='已全部标记为已读')


class SellerAppealMineView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        tenant = request.tenant
        appeals = TenantAppeal.objects.filter(tenant=tenant).prefetch_related('messages').order_by('-id')[:20]
        return success_response(data=SellerAppealDetailSerializer(appeals, many=True).data)


class SellerAppealDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request, pk: int) -> Response:
        appeal = TenantAppeal.objects.filter(
            tenant=request.tenant,
            pk=pk,
        ).prefetch_related('messages').first()
        if appeal is None:
            return error_response('申诉不存在', http_status=404)
        return success_response(data=SellerAppealDetailSerializer(appeal).data)


class SellerAppealReplyView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def post(self, request: Request, pk: int) -> Response:
        appeal = TenantAppeal.objects.filter(tenant=request.tenant, pk=pk).first()
        if appeal is None:
            return error_response('申诉不存在', http_status=404)
        content = str(request.data.get('content', '')).strip()
        if not content:
            return error_response('请填写回复内容')
        from tenants.notify import record_merchant_appeal_reply

        record_merchant_appeal_reply(appeal=appeal, user=request.user, content=content)
        appeal = TenantAppeal.objects.filter(pk=appeal.pk).prefetch_related('messages').first()
        return success_response(
            data=SellerAppealDetailSerializer(appeal).data,
            message='回复已发送',
        )
