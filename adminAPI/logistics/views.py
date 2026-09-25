"""Logistics API views."""

import logging

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.response import error_response, success_response
from customers.utils import get_request_customer
from logistics.express_companies import EXPRESS_COMPANIES, normalize_express_code
from logistics.models import Logistics
from logistics.serializers import LogisticsSerializer
from logistics.services import apply_tracking_result, sync_logistics_tracking
from orders.models import Order
from orders.role_filters import apply_order_role_filter

logger = logging.getLogger(__name__)


class ExpressCompaniesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return success_response(data=EXPRESS_COMPANIES)


class LogisticsTrackView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, order_id: int) -> Response:
        try:
            order = Order.objects.select_related('logistics').get(pk=order_id)
        except Order.DoesNotExist:
            return error_response('订单不存在', http_status=404)

        customer = get_request_customer(request)
        if customer:
            if order.customer_id != customer.id:
                return error_response('无权查看该订单物流', http_status=403)
        else:
            scoped = apply_order_role_filter(Order.objects.filter(pk=order_id), request.user)
            if not scoped.exists():
                return error_response('无权查看该订单物流', http_status=403)

        try:
            logistics = order.logistics
        except Logistics.DoesNotExist:
            if not order.logistics_no:
                return error_response('该订单暂无物流信息', http_status=404)
            return success_response(data={
                'express_company': '',
                'express_code': '',
                'tracking_number': order.logistics_no,
                'status': Logistics.STATUS_PENDING,
                'status_label': '待发货',
                'traces': [],
            })

        refresh = request.query_params.get('refresh', '').lower() in {'1', 'true', 'yes'}
        # Mock mode: only admin/staff refresh advances stage; client reads DB as-is.
        should_advance = refresh and not customer
        try:
            sync_logistics_tracking(logistics, force=refresh, advance=should_advance)
        except Exception:
            logger.exception('Sync logistics failed for order %s', order_id)

        return success_response(data=LogisticsSerializer(logistics).data)


class LogisticsWebhookView(APIView):
    """Kuaidi100 push callback (reserved for paid tier)."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        payload = request.data if isinstance(request.data, dict) else {}
        tracking_number = payload.get('lastResult', {}).get('nu') or payload.get('nu')
        express_code = payload.get('lastResult', {}).get('com') or payload.get('com')
        if not tracking_number:
            return success_response(message='ignored')

        normalized_code = normalize_express_code(express_code or '')
        logistics = Logistics.objects.filter(
            tracking_number=tracking_number,
            express_code=normalized_code,
        ).first()
        if not logistics:
            return success_response(message='no match')

        last_result = payload.get('lastResult') or payload
        traces = []
        for item in last_result.get('data') or []:
            traces.append({
                'time': item.get('ftime') or item.get('time'),
                'content': item.get('context', ''),
                'status': item.get('status'),
                'area': item.get('areaName') or '',
            })
        from logistics.services import map_kuaidi100_state

        apply_tracking_result(logistics, {
            'status': map_kuaidi100_state(last_result.get('state')),
            'traces': traces,
            'raw': last_result,
        })
        return success_response(message='ok')
