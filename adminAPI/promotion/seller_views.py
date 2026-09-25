"""Seller portal promotion API views — tenant-scoped."""

from __future__ import annotations

import logging

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination
from common.response import error_response, success_response
from products.models import Product
from promotion.models import Coupon, GroupBuyActivity, GroupOrder, SeckillActivity
from promotion.serializers import (
    CouponSerializer,
    GroupBuyActivitySerializer,
    GroupOrderSerializer,
    SeckillActivitySerializer,
)
from promotion.view_helpers import filter_activity_queryset, serializer_error_message
from tenants.seller_permissions import IsTenantStaffMember

logger = logging.getLogger(__name__)

EDITABLE_ACTIVITY_STATUSES = {
    SeckillActivity.STATUS_PENDING,
    SeckillActivity.STATUS_REVIEWING,
}


def _validate_tenant_products(tenant, product_ids: list[int]) -> Response | None:
    if not product_ids:
        return None
    unique_ids = list(set(product_ids))
    found = Product.all_objects.filter(tenant=tenant, id__in=unique_ids, is_active=True).count()
    if found != len(unique_ids):
        return error_response('请选择本店在售商品')
    return None


def _get_tenant_seckill(tenant, pk: int):
    return (
        SeckillActivity.all_objects.filter(tenant=tenant, pk=pk)
        .prefetch_related('products')
        .select_related('created_by', 'approved_by')
        .first()
    )


def _get_tenant_groupbuy(tenant, pk: int):
    return (
        GroupBuyActivity.all_objects.filter(tenant=tenant, pk=pk)
        .select_related('product', 'created_by', 'approved_by')
        .first()
    )


def _get_tenant_coupon(tenant, pk: int):
    return (
        Coupon.all_objects.filter(tenant=tenant, pk=pk)
        .prefetch_related('applicable_products')
        .select_related('applicable_category', 'created_by')
        .first()
    )


class SellerSeckillListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        queryset = (
            SeckillActivity.all_objects.filter(tenant=request.tenant)
            .prefetch_related('products')
            .select_related('created_by', 'approved_by')
        )
        queryset = filter_activity_queryset(queryset, request)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset.order_by('-id'), request)
        serializer = SeckillActivitySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        product_ids = request.data.get('product_ids') or []
        err = _validate_tenant_products(request.tenant, product_ids)
        if err:
            return err
        serializer = SeckillActivitySerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer_error_message(serializer))
        try:
            instance = serializer.save(
                tenant=request.tenant,
                created_by=request.user,
                status=SeckillActivity.STATUS_PENDING,
            )
        except Exception:
            logger.exception('Seller create seckill failed')
            return error_response('创建失败', code=50000, http_status=500)
        return success_response(
            data=SeckillActivitySerializer(instance).data,
            message='创建成功',
            http_status=status.HTTP_201_CREATED,
        )


class SellerSeckillDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request, pk: int) -> Response:
        activity = _get_tenant_seckill(request.tenant, pk)
        if activity is None:
            return error_response('活动不存在', http_status=404)
        return success_response(data=SeckillActivitySerializer(activity).data)

    def put(self, request: Request, pk: int) -> Response:
        activity = _get_tenant_seckill(request.tenant, pk)
        if activity is None:
            return error_response('活动不存在', http_status=404)
        if activity.status not in EDITABLE_ACTIVITY_STATUSES:
            return error_response('当前状态不可编辑')
        product_ids = request.data.get('product_ids')
        if product_ids is not None:
            err = _validate_tenant_products(request.tenant, product_ids)
            if err:
                return err
        serializer = SeckillActivitySerializer(activity, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(serializer_error_message(serializer))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Seller update seckill failed')
            return error_response('更新失败', code=50000, http_status=500)
        return success_response(data=SeckillActivitySerializer(instance).data, message='更新成功')

    def delete(self, request: Request, pk: int) -> Response:
        activity = _get_tenant_seckill(request.tenant, pk)
        if activity is None:
            return error_response('活动不存在', http_status=404)
        if activity.status not in {SeckillActivity.STATUS_PENDING, SeckillActivity.STATUS_CANCELLED}:
            return error_response('仅待审核或已取消的活动可删除')
        activity.delete()
        return success_response(message='删除成功')


class SellerSeckillSubmitView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def post(self, request: Request, pk: int) -> Response:
        activity = _get_tenant_seckill(request.tenant, pk)
        if activity is None:
            return error_response('活动不存在', http_status=404)
        if activity.status != SeckillActivity.STATUS_PENDING:
            return error_response('仅待审核的活动可提交')
        activity.status = SeckillActivity.STATUS_REVIEWING
        activity.reject_reason = ''
        activity.save(update_fields=['status', 'reject_reason', 'updated_at'])
        return success_response(data=SeckillActivitySerializer(activity).data, message='已提交审核')


class SellerSeckillCancelView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def post(self, request: Request, pk: int) -> Response:
        activity = _get_tenant_seckill(request.tenant, pk)
        if activity is None:
            return error_response('活动不存在', http_status=404)
        if activity.status in {SeckillActivity.STATUS_ENDED, SeckillActivity.STATUS_CANCELLED}:
            return error_response('活动已结束或已取消')
        activity.status = SeckillActivity.STATUS_CANCELLED
        activity.save(update_fields=['status', 'updated_at'])
        return success_response(data=SeckillActivitySerializer(activity).data, message='活动已终止')


class SellerGroupBuyListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        queryset = (
            GroupBuyActivity.all_objects.filter(tenant=request.tenant)
            .select_related('product', 'created_by', 'approved_by')
        )
        queryset = filter_activity_queryset(queryset, request)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset.order_by('-id'), request)
        serializer = GroupBuyActivitySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        product_id = request.data.get('product_id')
        if product_id:
            err = _validate_tenant_products(request.tenant, [product_id])
            if err:
                return err
        serializer = GroupBuyActivitySerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer_error_message(serializer))
        try:
            instance = serializer.save(
                tenant=request.tenant,
                created_by=request.user,
                status=GroupBuyActivity.STATUS_PENDING,
            )
        except Exception:
            logger.exception('Seller create groupbuy failed')
            return error_response('创建失败', code=50000, http_status=500)
        return success_response(
            data=GroupBuyActivitySerializer(instance).data,
            message='创建成功',
            http_status=status.HTTP_201_CREATED,
        )


class SellerGroupBuyDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request, pk: int) -> Response:
        activity = _get_tenant_groupbuy(request.tenant, pk)
        if activity is None:
            return error_response('活动不存在', http_status=404)
        return success_response(data=GroupBuyActivitySerializer(activity).data)

    def put(self, request: Request, pk: int) -> Response:
        activity = _get_tenant_groupbuy(request.tenant, pk)
        if activity is None:
            return error_response('活动不存在', http_status=404)
        if activity.status not in EDITABLE_ACTIVITY_STATUSES:
            return error_response('当前状态不可编辑')
        product_id = request.data.get('product_id')
        if product_id is not None:
            err = _validate_tenant_products(request.tenant, [product_id])
            if err:
                return err
        serializer = GroupBuyActivitySerializer(activity, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(serializer_error_message(serializer))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Seller update groupbuy failed')
            return error_response('更新失败', code=50000, http_status=500)
        return success_response(data=GroupBuyActivitySerializer(instance).data, message='更新成功')

    def delete(self, request: Request, pk: int) -> Response:
        activity = _get_tenant_groupbuy(request.tenant, pk)
        if activity is None:
            return error_response('活动不存在', http_status=404)
        if activity.status not in {GroupBuyActivity.STATUS_PENDING, GroupBuyActivity.STATUS_CANCELLED}:
            return error_response('仅待审核或已取消的活动可删除')
        activity.delete()
        return success_response(message='删除成功')


class SellerGroupBuySubmitView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def post(self, request: Request, pk: int) -> Response:
        activity = _get_tenant_groupbuy(request.tenant, pk)
        if activity is None:
            return error_response('活动不存在', http_status=404)
        if activity.status != GroupBuyActivity.STATUS_PENDING:
            return error_response('仅待审核的活动可提交')
        activity.status = GroupBuyActivity.STATUS_REVIEWING
        activity.reject_reason = ''
        activity.save(update_fields=['status', 'reject_reason', 'updated_at'])
        return success_response(data=GroupBuyActivitySerializer(activity).data, message='已提交审核')


class SellerGroupBuyCancelView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def post(self, request: Request, pk: int) -> Response:
        activity = _get_tenant_groupbuy(request.tenant, pk)
        if activity is None:
            return error_response('活动不存在', http_status=404)
        if activity.status in {GroupBuyActivity.STATUS_ENDED, GroupBuyActivity.STATUS_CANCELLED}:
            return error_response('活动已结束或已取消')
        activity.status = GroupBuyActivity.STATUS_CANCELLED
        activity.save(update_fields=['status', 'updated_at'])
        return success_response(data=GroupBuyActivitySerializer(activity).data, message='活动已终止')


class SellerGroupOrderListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request, pk: int) -> Response:
        activity = _get_tenant_groupbuy(request.tenant, pk)
        if activity is None:
            return error_response('活动不存在', http_status=404)
        queryset = GroupOrder.objects.filter(activity=activity).select_related(
            'order', 'captain', 'activity',
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset.order_by('-id'), request)
        serializer = GroupOrderSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class SellerCouponListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        queryset = (
            Coupon.all_objects.filter(tenant=request.tenant)
            .prefetch_related('applicable_products')
            .select_related('applicable_category', 'created_by')
        )
        status_param = request.query_params.get('status')
        keyword = request.query_params.get('keyword')
        coupon_type = request.query_params.get('coupon_type')
        if status_param:
            queryset = queryset.filter(status=status_param)
        if keyword:
            queryset = queryset.filter(name__icontains=keyword)
        if coupon_type:
            queryset = queryset.filter(coupon_type=coupon_type)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset.order_by('-id'), request)
        serializer = CouponSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        scope = request.data.get('applicable_scope')
        if scope == 'product':
            err = _validate_tenant_products(request.tenant, request.data.get('product_ids') or [])
            if err:
                return err
        serializer = CouponSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer_error_message(serializer))
        try:
            instance = serializer.save(
                tenant=request.tenant,
                created_by=request.user,
                status=Coupon.STATUS_DRAFT,
            )
        except Exception:
            logger.exception('Seller create coupon failed')
            return error_response('创建失败', code=50000, http_status=500)
        return success_response(
            data=CouponSerializer(instance).data,
            message='创建成功',
            http_status=status.HTTP_201_CREATED,
        )


class SellerCouponDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request, pk: int) -> Response:
        coupon = _get_tenant_coupon(request.tenant, pk)
        if coupon is None:
            return error_response('优惠券不存在', http_status=404)
        return success_response(data=CouponSerializer(coupon).data)

    def put(self, request: Request, pk: int) -> Response:
        coupon = _get_tenant_coupon(request.tenant, pk)
        if coupon is None:
            return error_response('优惠券不存在', http_status=404)
        if coupon.status not in {Coupon.STATUS_DRAFT, Coupon.STATUS_DISABLED}:
            return error_response('仅草稿或已停用的优惠券可编辑')
        scope = request.data.get('applicable_scope', coupon.applicable_scope)
        if scope == 'product':
            product_ids = request.data.get('product_ids')
            if product_ids is not None:
                err = _validate_tenant_products(request.tenant, product_ids)
                if err:
                    return err
        serializer = CouponSerializer(coupon, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(serializer_error_message(serializer))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Seller update coupon failed')
            return error_response('更新失败', code=50000, http_status=500)
        return success_response(data=CouponSerializer(instance).data, message='更新成功')

    def delete(self, request: Request, pk: int) -> Response:
        coupon = _get_tenant_coupon(request.tenant, pk)
        if coupon is None:
            return error_response('优惠券不存在', http_status=404)
        if coupon.status != Coupon.STATUS_DRAFT:
            return error_response('仅草稿状态的优惠券可删除')
        coupon.delete()
        return success_response(message='删除成功')


class SellerCouponPublishView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def post(self, request: Request, pk: int) -> Response:
        coupon = _get_tenant_coupon(request.tenant, pk)
        if coupon is None:
            return error_response('优惠券不存在', http_status=404)
        if coupon.status != Coupon.STATUS_DRAFT:
            return error_response('仅草稿状态的优惠券可发布')
        coupon.status = Coupon.STATUS_PUBLISHED
        coupon.save(update_fields=['status', 'updated_at'])
        return success_response(data=CouponSerializer(coupon).data, message='发布成功')


class SellerCouponDisableView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def post(self, request: Request, pk: int) -> Response:
        coupon = _get_tenant_coupon(request.tenant, pk)
        if coupon is None:
            return error_response('优惠券不存在', http_status=404)
        if coupon.status != Coupon.STATUS_PUBLISHED:
            return error_response('仅已发布的优惠券可停用')
        coupon.status = Coupon.STATUS_DISABLED
        coupon.save(update_fields=['status', 'updated_at'])
        return success_response(data=CouponSerializer(coupon).data, message='已停用')
