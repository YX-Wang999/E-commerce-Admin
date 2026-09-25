"""Points mall customer API."""

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination
from common.response import error_response, success_response
from customers.permissions import IsCustomerAuthenticated
from customers.utils import get_request_customer
from points.services import get_profile
from points_mall.models import PointsMallOrder
from points_mall.serializers import serialize_item, serialize_order
from points_mall.services import ExchangeError, exchange_item, get_item, hot_items, list_items


class PointsMallItemListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        item_type = (request.query_params.get('type') or 'all').strip()
        category = (request.query_params.get('category') or '').strip()
        sort = (request.query_params.get('sort') or 'default').strip()
        keyword = (request.query_params.get('keyword') or '').strip()
        qs = list_items(
            item_type=item_type or None,
            category=category or None,
            keyword=keyword or None,
            sort=sort or None,
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        items = [serialize_item(item) for item in page]
        data = paginator.get_paginated_response(items).data
        profile = None
        customer = get_request_customer(request)
        if customer:
            profile = get_profile(customer)
        data['profile'] = profile
        data['hot_items'] = [serialize_item(item) for item in hot_items(5)]
        return Response(data)


class PointsMallItemDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request, pk: int) -> Response:
        try:
            item = get_item(pk)
        except ExchangeError as exc:
            return error_response(str(exc), http_status=404)
        return success_response(data=serialize_item(item))


class PointsMallExchangeView(APIView):
    permission_classes = [IsCustomerAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        quantity = int(request.data.get('quantity') or 1)
        address = request.data.get('address') or {}
        try:
            order = exchange_item(
                request.customer,
                pk,
                quantity=quantity,
                address=address,
            )
        except ExchangeError as exc:
            return error_response(str(exc))
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(data=serialize_order(order), message='兑换成功')


class PointsMallOrderListView(APIView):
    permission_classes = [IsCustomerAuthenticated]

    def get(self, request: Request) -> Response:
        qs = PointsMallOrder.objects.filter(customer=request.customer).select_related('item', 'customer')
        status_filter = (request.query_params.get('status') or '').strip()
        if status_filter:
            qs = qs.filter(status=status_filter)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        items = [serialize_order(row) for row in page]
        return paginator.get_paginated_response(items)


class PointsMallOrderDetailView(APIView):
    permission_classes = [IsCustomerAuthenticated]

    def get(self, request: Request, pk: int) -> Response:
        order = PointsMallOrder.objects.select_related('item', 'customer').filter(
            pk=pk,
            customer=request.customer,
        ).first()
        if order is None:
            return error_response('订单不存在', http_status=404)
        return success_response(data=serialize_order(order))
