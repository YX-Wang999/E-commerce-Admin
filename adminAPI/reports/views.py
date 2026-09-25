"""Report and dashboard statistics."""

import logging
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.response import success_response
from customers.models import Customer
from feedback.models import CustomerFeedback
from orders.models import Order, Refund
from products.models import Product

logger = logging.getLogger(__name__)

LOW_STOCK_THRESHOLD = 10


def _money(value) -> str:
    """Format decimal amounts to two fixed digits."""
    amount = Decimal(str(value or 0))
    return f'{amount.quantize(Decimal("0.01")):.2f}'


TODO_VISIBILITY: dict[str, set[str]] = {
    'super_admin': {
        'pending_orders',
        'pending_refunds',
        'low_stock_products',
        'pending_promotions',
        'pending_reviews',
        'pending_tenant_appeals',
    },
    'ops_director': {
        'pending_orders',
        'pending_refunds',
        'low_stock_products',
        'pending_promotions',
        'pending_reviews',
        'pending_tenant_appeals',
    },
    'ops_manager': {'pending_orders', 'low_stock_products', 'pending_promotions'},
    'ops_staff': {'pending_orders', 'low_stock_products', 'pending_promotions'},
    'cs_staff': {'pending_refunds', 'pending_reviews'},
    'warehouse_manager': {'pending_orders', 'low_stock_products'},
    'data_analyst': set(),
    'dept_manager': set(),
    'employee': set(),
}


def _resolve_role_codes(user) -> set[str]:
    """Get active role codes for user."""
    if user.is_superuser:
        return {'super_admin'}
    return set(user.roles.filter(is_active=True).values_list('code', flat=True))


def _today_range():
    """Return today start/end datetimes."""
    now = timezone.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, now


def _compute_todo_counts() -> dict[str, int]:
    """Aggregate dashboard todo counters."""
    from promotion.models import GroupBuyActivity, SeckillActivity
    from tenants.models import TenantAppeal

    return {
        'pending_orders': Order.objects.filter(status=Order.STATUS_PAID).count(),
        'pending_refunds': Refund.objects.filter(status=Refund.STATUS_PENDING).count(),
        'low_stock_products': Product.objects.filter(
            stock__lte=LOW_STOCK_THRESHOLD,
            status=Product.STATUS_ON_SALE,
        ).count(),
        'pending_promotions': (
            SeckillActivity.objects.filter(status=SeckillActivity.STATUS_REVIEWING).count()
            + GroupBuyActivity.objects.filter(status=GroupBuyActivity.STATUS_REVIEWING).count()
        ),
        'pending_reviews': CustomerFeedback.objects.filter(
            status=CustomerFeedback.STATUS_PENDING,
        ).count(),
        'pending_tenant_appeals': TenantAppeal.objects.filter(
            status__in=[TenantAppeal.STATUS_PENDING, TenantAppeal.STATUS_PROCESSING],
        ).count(),
    }


def _resolve_visible_todo_keys(roles: set[str]) -> list[str]:
    """Resolve todo keys visible to the given roles."""
    visible: set[str] = set()
    for role in roles:
        visible |= TODO_VISIBILITY.get(role, set())
    order = [
        'pending_orders',
        'pending_refunds',
        'low_stock_products',
        'pending_promotions',
        'pending_reviews',
        'pending_tenant_appeals',
    ]
    return [key for key in order if key in visible]


class DashboardTodosView(APIView):
    """Role-based dashboard todo summary."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return todo counts and visible keys for current user."""
        roles = _resolve_role_codes(request.user)
        counts = _compute_todo_counts()
        visible = _resolve_visible_todo_keys(roles)
        return success_response(data={
            **counts,
            'visible': visible,
        })


class DashboardSummaryView(APIView):
    """Role-based dashboard summary."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return dashboard cards and todos by role."""
        user = request.user
        roles = _resolve_role_codes(user)
        today_start, _ = _today_range()

        product_count = Product.all_objects.filter(is_active=True).count()
        order_count = Order.all_objects.count()
        customer_count = (
            Order.all_objects.exclude(customer_id__isnull=True)
            .values('customer_id')
            .distinct()
            .count()
        )
        today_income = Order.all_objects.filter(
            created_at__gte=today_start,
            status__in=[Order.STATUS_PAID, Order.STATUS_SHIPPED, Order.STATUS_COMPLETED],
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        pending_ship = Order.all_objects.filter(status=Order.STATUS_PAID).count()
        pending_refund = Refund.objects.filter(status=Refund.STATUS_PENDING).count()
        low_stock = Product.all_objects.filter(stock__lte=LOW_STOCK_THRESHOLD, status=Product.STATUS_ON_SALE).count()
        today_orders = Order.all_objects.filter(created_at__gte=today_start).count()
        cancelled_orders = Order.all_objects.filter(status=Order.STATUS_CANCELLED).count()
        total_revenue = (
            Order.all_objects.filter(
                status__in=[Order.STATUS_PAID, Order.STATUS_SHIPPED, Order.STATUS_COMPLETED],
            ).aggregate(total=Sum('total_amount'))['total']
            or Decimal('0')
        )

        cards = []

        if 'super_admin' in roles:
            cards = [
                {'key': 'products', 'label': '商品总数', 'value': product_count},
                {'key': 'orders', 'label': '订单总数', 'value': order_count},
                {'key': 'customers', 'label': '客户总数', 'value': customer_count},
                {'key': 'today_income', 'label': '今日收入', 'value': _money(today_income)},
                {'key': 'cancelled_orders', 'label': '取消订单', 'value': cancelled_orders},
            ]
        elif 'ops_director' in roles:
            cards = [
                {'key': 'today_orders', 'label': '今日订单', 'value': today_orders},
                {'key': 'pending_ship', 'label': '待发货', 'value': pending_ship},
                {'key': 'today_income', 'label': '今日收入', 'value': _money(today_income)},
                {'key': 'total_revenue', 'label': '总收入', 'value': _money(total_revenue)},
                {'key': 'cancelled_orders', 'label': '取消订单', 'value': cancelled_orders},
                {'key': 'customers', 'label': '客户总数', 'value': customer_count},
            ]
        elif 'ops_manager' in roles:
            cards = [
                {'key': 'today_orders', 'label': '今日订单', 'value': today_orders},
                {'key': 'pending_ship', 'label': '待发货', 'value': pending_ship},
                {'key': 'today_income', 'label': '今日收入', 'value': _money(today_income)},
                {'key': 'total_revenue', 'label': '总收入', 'value': _money(total_revenue)},
                {'key': 'cancelled_orders', 'label': '取消订单', 'value': cancelled_orders},
                {'key': 'customers', 'label': '客户总数', 'value': customer_count},
                {'key': 'low_stock', 'label': '低库存商品', 'value': low_stock},
            ]
        elif 'ops_staff' in roles:
            cards = [
                {'key': 'pending_orders', 'label': '待处理订单', 'value': pending_ship},
                {'key': 'low_stock', 'label': '库存预警', 'value': low_stock},
            ]
        elif 'cs_staff' in roles:
            cards = [
                {'key': 'pending_refund', 'label': '待处理售后', 'value': pending_refund},
            ]
        elif 'data_analyst' in roles:
            cards = [
                {'key': 'today_orders', 'label': '今日订单', 'value': today_orders},
                {'key': 'today_income', 'label': '今日收入', 'value': _money(today_income)},
                {'key': 'cancelled_orders', 'label': '取消订单', 'value': cancelled_orders},
            ]
        elif 'warehouse_manager' in roles:
            cards = [
                {'key': 'pending_ship', 'label': '待发货订单', 'value': pending_ship},
                {'key': 'low_stock', 'label': '库存预警', 'value': low_stock},
            ]
        else:
            cards = [
                {'key': 'today_orders', 'label': '今日订单', 'value': today_orders},
            ]

        return success_response(data={
            'roles': list(roles),
            'cards': cards,
        })


class SalesReportView(APIView):
    """Sales statistics."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return sales trend for last 7 days."""
        start = timezone.now() - timedelta(days=6)
        trend = (
            Order.objects.filter(created_at__gte=start)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(
                order_count=Count('id'),
                amount=Sum('total_amount'),
            )
            .order_by('day')
        )
        return success_response(data={
            'trend': [
                {
                    'date': item['day'].isoformat() if item['day'] else '',
                    'order_count': item['order_count'],
                    'amount': str(item['amount'] or Decimal('0')),
                }
                for item in trend
            ],
        })


class ProductRankView(APIView):
    """Product sales ranking."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return top selling products."""
        from orders.models import OrderItem

        limit = min(int(request.query_params.get('limit', 10)), 50)
        ranking = (
            OrderItem.objects.values('product__name')
            .annotate(total_qty=Sum('quantity'), total_amount=Sum('unit_price'))
            .order_by('-total_qty')[:limit]
        )
        return success_response(data={
            'ranking': [
                {
                    'product_name': item['product__name'],
                    'total_qty': item['total_qty'],
                    'total_amount': str(item['total_amount'] or Decimal('0')),
                }
                for item in ranking
            ],
        })


class HasReportFinance(BasePermission):
    """Allow finance report for superuser or report:finance permission."""

    message = '无权查看财务汇总'

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.roles.filter(
            is_active=True,
            permissions__code='report:finance',
        ).exists()


class CustomerAnalysisView(APIView):
    """Customer growth and activity analysis."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return customer metrics and growth trend."""
        start = timezone.now() - timedelta(days=6)
        total = Customer.objects.filter(is_active=True).count()
        with_orders = Customer.objects.filter(orders__isnull=False).distinct().count()
        repeat_customers = (
            Customer.objects.annotate(order_total=Count('orders'))
            .filter(order_total__gte=2)
            .count()
        )
        growth = (
            Customer.objects.filter(created_at__gte=start)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(new_count=Count('id'))
            .order_by('day')
        )
        repeat_rate = round(repeat_customers / with_orders * 100, 1) if with_orders else 0
        return success_response(data={
            'summary': {
                'total_customers': total,
                'customers_with_orders': with_orders,
                'repeat_customers': repeat_customers,
                'repeat_rate': repeat_rate,
            },
            'growth': [
                {
                    'date': item['day'].isoformat() if item['day'] else '',
                    'new_count': item['new_count'],
                }
                for item in growth
            ],
        })


class PromotionAnalysisView(APIView):
    """Promotion activity statistics."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return promotion counts grouped by type and status."""
        from promotion.models import Coupon, GroupBuyActivity, SeckillActivity

        def count_by_status(model):
            return {
                item['status']: item['count']
                for item in model.objects.values('status').annotate(count=Count('id'))
            }

        seckill = count_by_status(SeckillActivity)
        groupbuy = count_by_status(GroupBuyActivity)
        coupon = count_by_status(Coupon)
        return success_response(data={
            'seckill': seckill,
            'groupbuy': groupbuy,
            'coupon': coupon,
            'totals': {
                'seckill': sum(seckill.values()),
                'groupbuy': sum(groupbuy.values()),
                'coupon': sum(coupon.values()),
            },
        })


class FinanceSummaryView(APIView):
    """Revenue and finance summary."""

    permission_classes = [IsAuthenticated, HasReportFinance]

    def get(self, request: Request) -> Response:
        """Return revenue summary and monthly trend."""
        paid_statuses = [Order.STATUS_PAID, Order.STATUS_SHIPPED, Order.STATUS_COMPLETED]
        agg = Order.objects.filter(status__in=paid_statuses).aggregate(
            total_amount=Sum('total_amount'),
            order_count=Count('id'),
        )
        total_amount = agg['total_amount'] or Decimal('0')
        order_count = agg['order_count'] or 0
        avg_amount = total_amount / order_count if order_count else Decimal('0')

        start = timezone.now() - timedelta(days=29)
        trend = (
            Order.objects.filter(created_at__gte=start, status__in=paid_statuses)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(amount=Sum('total_amount'), order_count=Count('id'))
            .order_by('day')
        )
        by_status = {
            item['status']: {
                'count': item['count'],
                'amount': str(item['amount'] or Decimal('0')),
            }
            for item in Order.objects.values('status').annotate(
                count=Count('id'),
                amount=Sum('total_amount'),
            )
        }
        return success_response(data={
            'summary': {
                'total_revenue': str(total_amount),
                'order_count': order_count,
                'avg_order_amount': str(round(avg_amount, 2)),
            },
            'trend': [
                {
                    'date': item['day'].isoformat() if item['day'] else '',
                    'amount': str(item['amount'] or Decimal('0')),
                    'order_count': item['order_count'],
                }
                for item in trend
            ],
            'by_status': by_status,
        })
