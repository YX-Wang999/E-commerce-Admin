"""Points API views."""

import logging

from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination
from common.response import error_response, success_response
from common.tenant import TenantViewSetMixin
from customers.models import Customer
from customers.permissions import IsCustomerAuthenticated
from customers.utils import get_request_customer
from points.models import PointsAccount, PointsRule, PointsTransaction
from points.permissions import HasPointsAdjust, HasPointsRead, HasPointsRule
from points.serializers import (
    PointsAccountSerializer,
    PointsAdjustSerializer,
    PointsRuleSerializer,
    PointsRuleWriteSerializer,
    PointsTransactionSerializer,
)
from points.services import change_points, get_profile, sign_in
from points.checkout import get_checkout_points_info

logger = logging.getLogger(__name__)


class PointsCheckoutView(APIView):
    """Checkout page points deduction info."""

    permission_classes = [IsCustomerAuthenticated]

    def get(self, request: Request) -> Response:
        from cart.models import CartItem
        from decimal import Decimal

        cart_items = CartItem.objects.select_related('product', 'cart').filter(
            cart__customer=request.customer,
            selected=True,
        )
        subtotal = sum(
            Decimal(str(item.product.price)) * item.quantity for item in cart_items
        )
        if subtotal <= 0:
            cart_items = CartItem.objects.select_related('product', 'cart').filter(
                cart__customer=request.customer,
            )
            subtotal = sum(
                Decimal(str(item.product.price)) * item.quantity for item in cart_items
            )
        order_amount = request.query_params.get('order_amount')
        if order_amount:
            subtotal = Decimal(str(order_amount))
        return success_response(data=get_checkout_points_info(request.customer, subtotal))


class PointsProfileView(APIView):
    """Mall customer points profile."""

    permission_classes = [IsCustomerAuthenticated]

    def get(self, request: Request) -> Response:
        return success_response(data=get_profile(request.customer))


class PointsSignInView(APIView):
    """Daily sign-in for mall customer."""

    permission_classes = [IsCustomerAuthenticated]

    def post(self, request: Request) -> Response:
        try:
            result = sign_in(request.customer)
        except ValueError as exc:
            return error_response(str(exc))
        except Exception:
            logger.exception('Sign in failed')
            return error_response('签到失败', code=50000, http_status=500)
        return success_response(
            data={
                'points_earned': result['points_earned'],
                'consecutive_days': result['consecutive_days'],
                'balance': result['balance'],
            },
            message='签到成功',
        )


class PointsMallTransactionsView(APIView):
    """Mall customer transaction list."""

    permission_classes = [IsCustomerAuthenticated]

    def get(self, request: Request) -> Response:
        queryset = PointsTransaction.objects.filter(customer=request.customer).order_by('-id')
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = PointsTransactionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class PointsPublicRulesView(APIView):
    """Active rules for mall display."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        rules = PointsRule.objects.filter(is_active=True).order_by('code')
        return success_response(data=PointsRuleSerializer(rules, many=True).data)


class PointsAdjustView(APIView):
    """Admin manual points adjustment."""

    permission_classes = [IsAuthenticated, HasPointsAdjust]

    def post(self, request: Request) -> Response:
        serializer = PointsAdjustSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        customer = Customer.objects.get(pk=serializer.validated_data['customer_id'])
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description') or '管理员手动调整'
        try:
            suffix = txn_placeholder()
            txn = change_points(
                customer,
                amount,
                PointsTransaction.TYPE_ADJUST_ADMIN,
                source=f'adjust:{request.user.id}:{suffix}',
                description=description,
            )
        except ValueError as exc:
            return error_response(str(exc))
        except Exception:
            logger.exception('Adjust points failed')
            return error_response('调整失败', code=50000, http_status=500)
        return success_response(
            data=PointsTransactionSerializer(txn).data,
            message='调整成功',
            http_status=status.HTTP_201_CREATED,
        )


def txn_placeholder() -> str:
    from django.utils import timezone
    return timezone.now().strftime('%Y%m%d%H%M%S%f')


class PointsAccountViewSet(TenantViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = PointsAccount.objects.select_related('customer').all()
    serializer_class = PointsAccountSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated, HasPointsRead]

    def get_queryset(self):
        queryset = super().get_queryset()
        keyword = self.request.query_params.get('keyword')
        if keyword:
            queryset = queryset.filter(
                Q(customer__name__icontains=keyword) | Q(customer__phone__icontains=keyword),
            )
        return queryset.order_by('-balance', '-updated_at')

    def list(self, request: Request, *args, **kwargs) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)


class PointsTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PointsTransaction.objects.select_related('customer').all()
    serializer_class = PointsTransactionSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated, HasPointsRead]

    def get_queryset(self):
        queryset = super().get_queryset()
        customer_id = self.request.query_params.get('customer_id')
        trans_type = self.request.query_params.get('trans_type')
        keyword = self.request.query_params.get('keyword')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        if trans_type:
            queryset = queryset.filter(trans_type=trans_type)
        if keyword:
            queryset = queryset.filter(
                Q(customer__name__icontains=keyword)
                | Q(customer__phone__icontains=keyword)
                | Q(description__icontains=keyword),
            )
        return queryset.order_by('-id')

    def list(self, request: Request, *args, **kwargs) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)


class PointsRuleViewSet(viewsets.ModelViewSet):
    queryset = PointsRule.objects.all().order_by('sort_order', 'id')
    serializer_class = PointsRuleSerializer
    pagination_class = StandardPagination
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated(), HasPointsRead()]
        return [IsAuthenticated(), HasPointsRule()]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return PointsRuleWriteSerializer
        return PointsRuleSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        rule_type = self.request.query_params.get('rule_type')
        if rule_type in ('earn', 'redeem'):
            queryset = queryset.filter(rule_type=rule_type)
        return queryset

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        if instance.is_system:
            return error_response('系统内置规则不可删除')
        instance.delete()
        return success_response(message='规则已删除')

    def list(self, request: Request, *args, **kwargs) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return success_response(data=self.get_serializer(self.get_object()).data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        instance = serializer.save()
        return success_response(
            data=PointsRuleSerializer(instance).data,
            message='规则已创建',
            http_status=status.HTTP_201_CREATED,
        )

    def update(self, request: Request, *args, **kwargs) -> Response:
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        instance = serializer.save()
        return success_response(data=PointsRuleSerializer(instance).data, message='更新成功')
