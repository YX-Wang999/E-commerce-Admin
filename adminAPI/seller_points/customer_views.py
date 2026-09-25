"""Customer-facing seller points checkout API."""

from decimal import Decimal, InvalidOperation

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.response import error_response, success_response
from customers.permissions import IsCustomerAuthenticated
from customers.utils import get_request_customer
from seller_points.checkout import get_checkout_seller_points_info
from tenants.models import Tenant


class CustomerSellerPointsCheckoutView(APIView):
    permission_classes = [IsCustomerAuthenticated]

    def get(self, request: Request) -> Response:
        customer = get_request_customer(request)
        if customer is None:
            return error_response('请先登录', http_status=401)
        tenant_id = request.query_params.get('tenant_id')
        order_amount_raw = request.query_params.get('order_amount')
        if not tenant_id or order_amount_raw is None:
            return error_response('缺少 tenant_id 或 order_amount')
        try:
            tenant = Tenant.objects.get(pk=int(tenant_id), status=Tenant.STATUS_ACTIVE)
            order_amount = Decimal(str(order_amount_raw))
        except (Tenant.DoesNotExist, InvalidOperation, ValueError):
            return error_response('参数无效')
        if order_amount < 0:
            return error_response('订单金额无效')
        info = get_checkout_seller_points_info(customer, tenant, order_amount)
        return success_response(data=info)
