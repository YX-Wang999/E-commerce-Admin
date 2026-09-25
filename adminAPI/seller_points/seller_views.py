"""Seller portal points API."""

from __future__ import annotations

from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination
from common.response import error_response, success_response
from customers.models import Customer
from seller_points.models import SellerPointsAccount, SellerPointsRule, SellerPointsTransaction
from seller_points.serializers import (
    SellerPointsAccountSerializer,
    SellerPointsAdjustSerializer,
    SellerPointsRuleSerializer,
    SellerPointsTransactionSerializer,
)
from seller_points.services import change_seller_points, clamp_rule_values, get_or_create_rule
from tenants.seller_permissions import IsTenantStaffMember


class SellerPointsRuleView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        rule = get_or_create_rule(request.tenant)
        return success_response(data=SellerPointsRuleSerializer(rule).data)

    def put(self, request: Request) -> Response:
        rule = get_or_create_rule(request.tenant)
        payload = clamp_rule_values(request.data)
        serializer = SellerPointsRuleSerializer(rule, data=payload, partial=True)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        serializer.save()
        return success_response(data=serializer.data, message='积分规则已保存')


class SellerPointsAccountListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        queryset = SellerPointsAccount.objects.filter(tenant=request.tenant).select_related('customer')
        keyword = (request.query_params.get('keyword') or '').strip()
        if keyword:
            queryset = queryset.filter(
                Q(customer__name__icontains=keyword) | Q(customer__phone__icontains=keyword),
            )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset.order_by('-balance', '-updated_at'), request)
        serializer = SellerPointsAccountSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class SellerPointsTransactionListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        queryset = SellerPointsTransaction.objects.filter(tenant=request.tenant).select_related('customer')
        customer_id = request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        keyword = (request.query_params.get('keyword') or '').strip()
        if keyword:
            queryset = queryset.filter(
                Q(customer__name__icontains=keyword)
                | Q(customer__phone__icontains=keyword)
                | Q(source_id__icontains=keyword),
            )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset.order_by('-id'), request)
        serializer = SellerPointsTransactionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class SellerPointsAdjustView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def post(self, request: Request) -> Response:
        serializer = SellerPointsAdjustSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        customer_id = serializer.validated_data['customer_id']
        amount = serializer.validated_data['amount']
        description = serializer.validated_data.get('description') or '商家手动调整'
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return error_response('客户不存在')
        try:
            txn = change_seller_points(
                request.tenant,
                customer,
                amount,
                SellerPointsTransaction.TYPE_ADMIN_ADJUST,
                source_id=f'adjust:{request.user.id}',
                description=description,
            )
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(
            data=SellerPointsTransactionSerializer(txn).data,
            message='积分调整成功',
        )
