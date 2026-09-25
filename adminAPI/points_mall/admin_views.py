"""Points mall admin API."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination
from common.response import error_response, success_response
from orders.role_filters import resolve_role_codes
from points_mall.models import PointsMallItem, PointsMallOrder
from points_mall.serializers import serialize_item, serialize_order
from points_mall.services import ExchangeError, mall_stats, ship_order


def _parse_datetime(value):
    from django.utils.dateparse import parse_datetime

    if not value:
        return None
    if isinstance(value, str):
        return parse_datetime(value.replace('Z', '+00:00'))
    return value


def _can_manage(user) -> bool:
    if getattr(user, 'is_superuser', False):
        return True
    roles = resolve_role_codes(user)
    return bool(roles & {'super_admin', 'ops_manager', 'ops_staff', 'ops_director'})


class AdminPointsMallItemListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        if not _can_manage(request.user):
            return error_response('无权查看', http_status=403)
        qs = PointsMallItem.objects.all()
        keyword = (request.query_params.get('keyword') or '').strip()
        item_type = (request.query_params.get('item_type') or '').strip()
        status = (request.query_params.get('status') or '').strip()
        if keyword:
            qs = qs.filter(name__icontains=keyword)
        if item_type:
            qs = qs.filter(item_type=item_type)
        if status:
            qs = qs.filter(status=status)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response([serialize_item(item) for item in page])

    def post(self, request: Request) -> Response:
        if not _can_manage(request.user):
            return error_response('无权操作', http_status=403)
        data = request.data
        item = PointsMallItem.objects.create(
            name=data.get('name', '').strip(),
            image=data.get('image', ''),
            description=data.get('description', ''),
            item_type=data.get('item_type', PointsMallItem.TYPE_PHYSICAL),
            points_required=int(data.get('points_required') or 0),
            stock=int(data.get('stock') or 0),
            per_user_limit=int(data.get('per_user_limit') or 1),
            requires_address=bool(data.get('requires_address')),
            is_hot=bool(data.get('is_hot')),
            is_limited_time=bool(data.get('is_limited_time')),
            start_at=_parse_datetime(data.get('start_at')),
            end_at=_parse_datetime(data.get('end_at')),
            status=data.get('status', PointsMallItem.STATUS_DRAFT),
            sort_order=int(data.get('sort_order') or 0),
        )
        return success_response(data=serialize_item(item), message='创建成功')


class AdminPointsMallItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, pk: int) -> Response:
        if not _can_manage(request.user):
            return error_response('无权操作', http_status=403)
        item = PointsMallItem.objects.filter(pk=pk).first()
        if item is None:
            return error_response('商品不存在', http_status=404)
        for field in (
            'name', 'image', 'description', 'item_type', 'status',
        ):
            if field in request.data:
                setattr(item, field, request.data[field])
        for field in ('start_at', 'end_at'):
            if field in request.data:
                setattr(item, field, _parse_datetime(request.data[field]))
        for field in ('points_required', 'stock', 'per_user_limit', 'sort_order'):
            if field in request.data:
                setattr(item, field, int(request.data[field]))
        for field in ('requires_address', 'is_hot', 'is_limited_time'):
            if field in request.data:
                setattr(item, field, bool(request.data[field]))
        item.save()
        return success_response(data=serialize_item(item), message='更新成功')

    def delete(self, request: Request, pk: int) -> Response:
        if not _can_manage(request.user):
            return error_response('无权操作', http_status=403)
        item = PointsMallItem.objects.filter(pk=pk).first()
        if item is None:
            return error_response('商品不存在', http_status=404)
        item.status = PointsMallItem.STATUS_OFF_SALE
        item.save(update_fields=['status', 'updated_at'])
        return success_response(message='已下架')


class AdminPointsMallOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        if not _can_manage(request.user):
            return error_response('无权查看', http_status=403)
        qs = PointsMallOrder.objects.select_related('item', 'customer')
        keyword = (request.query_params.get('keyword') or '').strip()
        status = (request.query_params.get('status') or '').strip()
        if keyword:
            qs = qs.filter(item_name__icontains=keyword)
        if status:
            qs = qs.filter(status=status)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response([serialize_order(row) for row in page])


class AdminPointsMallOrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, pk: int) -> Response:
        if not _can_manage(request.user):
            return error_response('无权查看', http_status=403)
        order = PointsMallOrder.objects.select_related('item', 'customer').filter(pk=pk).first()
        if order is None:
            return error_response('订单不存在', http_status=404)
        return success_response(data=serialize_order(order))


class AdminPointsMallOrderShipView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        if not _can_manage(request.user):
            return error_response('无权操作', http_status=403)
        try:
            order = ship_order(
                pk,
                logistics_company=request.data.get('logistics_company', ''),
                logistics_no=request.data.get('logistics_no', ''),
                remark=request.data.get('remark', ''),
            )
        except ExchangeError as exc:
            return error_response(str(exc))
        return success_response(data=serialize_order(order), message='发货成功')


class AdminPointsMallStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        if not _can_manage(request.user):
            return error_response('无权查看', http_status=403)
        return success_response(data=mall_stats())
