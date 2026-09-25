"""Platform admin order cancellation views."""

from __future__ import annotations

from django.db.models import Count
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.response import error_response, success_response
from orders.cancellation import cancel_order_by_platform, review_cancel_apply_by_platform
from orders.models import Order
from orders.role_filters import apply_order_role_filter
from orders.serializers import OrderCancelReviewSerializer, OrderCancelSerializer, OrderSerializer


class AdminOrderCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        if getattr(request, 'customer', None) is not None:
            return error_response('无权操作', http_status=403)

        queryset = apply_order_role_filter(Order.objects.all(), request.user)
        order = queryset.filter(pk=pk).first()
        if order is None:
            return error_response('订单不存在', http_status=404)

        serializer = OrderCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = cancel_order_by_platform(
                order,
                reason=serializer.validated_data['reason'],
                operator_id=str(request.user.id),
            )
        except ValueError as exc:
            return error_response(str(exc))

        return success_response(data=OrderSerializer(order).data, message='订单已取消')


class AdminOrderCancelReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        if getattr(request, 'customer', None) is not None:
            return error_response('无权操作', http_status=403)

        queryset = apply_order_role_filter(Order.objects.all(), request.user)
        order = queryset.filter(pk=pk).first()
        if order is None:
            return error_response('订单不存在', http_status=404)

        serializer = OrderCancelReviewSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message))

        try:
            order = review_cancel_apply_by_platform(
                order,
                approve=serializer.validated_data['approve'],
                remark=serializer.validated_data.get('remark', ''),
                operator_id=str(request.user.id),
            )
        except ValueError as exc:
            return error_response(str(exc))

        message = '已同意取消' if serializer.validated_data['approve'] else '已驳回取消申请'
        return success_response(data=OrderSerializer(order).data, message=message)


class AdminCancelStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        if getattr(request, 'customer', None) is not None:
            return error_response('无权操作', http_status=403)

        queryset = apply_order_role_filter(Order.objects.all(), request.user)
        cancelled = queryset.filter(status=Order.STATUS_CANCELLED)
        by_type = {
            row['cancel_type']: row['count']
            for row in cancelled.values('cancel_type').annotate(count=Count('id'))
        }
        return success_response(
            data={
                'cancelled_total': cancelled.count(),
                'canceling_count': queryset.filter(
                    status=Order.STATUS_PAID,
                    cancel_status=Order.CANCEL_STATUS_PENDING,
                ).count(),
                'by_cancel_type': by_type,
            },
        )
