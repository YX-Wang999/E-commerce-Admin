"""Promotion views."""

import logging

from django.db.models import Q
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from common.pagination import StandardPagination
from common.response import error_response, success_response
from common.tenant import TenantViewSetMixin
from promotion.models import Coupon, GroupBuyActivity, GroupOrder, SeckillActivity, UserCoupon
from promotion.permissions import (
    HasCouponCreate,
    HasCouponPublish,
    HasCouponRead,
    HasCouponUpdate,
    HasPromotionApprove,
    HasPromotionCancel,
    HasPromotionCreate,
    HasPromotionRead,
    HasPromotionSubmit,
    HasPromotionUpdate,
    user_has_permission,
)
from promotion.serializers import (
    CouponSerializer,
    GroupBuyActivitySerializer,
    GroupOrderSerializer,
    SeckillActivitySerializer,
    UserCouponSerializer,
)
from promotion.view_helpers import (
    create_response,
    filter_activity_queryset,
    list_response,
    serializer_error_message,
    update_response,
)

logger = logging.getLogger(__name__)

EDITABLE_APPROVAL_STATUSES = {
    SeckillActivity.STATUS_PENDING,
    SeckillActivity.STATUS_REVIEWING,
}


def _is_platform_staff(request: Request) -> bool:
    user = request.user
    customer = getattr(request, 'customer', None)
    return user.is_authenticated and hasattr(user, 'roles') and customer is None


def _filter_platform_promotion_list(queryset, request: Request, *, reviewing_status: str):
    """Platform list: own promotions + merchant items awaiting review."""
    if not _is_platform_staff(request) or request.query_params.get('all_tenants', '').lower() in ('1', 'true'):
        return queryset
    if request.query_params.get('tenant_id') or request.query_params.get('tenant_code'):
        return queryset
    return queryset.filter(
        Q(tenant__isnull=True) | Q(tenant__isnull=False, status=reviewing_status),
    )


def _filter_platform_coupon_list(queryset, request: Request):
    """Platform coupon list: platform-owned coupons only by default."""
    if not _is_platform_staff(request) or request.query_params.get('all_tenants', '').lower() in ('1', 'true'):
        return queryset
    if request.query_params.get('tenant_id') or request.query_params.get('tenant_code'):
        return queryset
    return queryset.filter(tenant__isnull=True)


class SeckillActivityViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """Seckill activity CRUD with approval workflow."""

    queryset = SeckillActivity.objects.prefetch_related('products').select_related(
        'created_by', 'approved_by',
    ).all()
    serializer_class = SeckillActivitySerializer
    pagination_class = StandardPagination

    def get_permissions(self):
        """Action-based permissions."""
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated(), HasPromotionRead()]
        if self.action == 'create':
            return [IsAuthenticated(), HasPromotionCreate()]
        if self.action in ('update', 'partial_update'):
            return [IsAuthenticated(), HasPromotionUpdate()]
        if self.action == 'destroy':
            return [IsAuthenticated(), HasPromotionCancel()]
        if self.action == 'submit':
            return [IsAuthenticated(), HasPromotionSubmit()]
        if self.action in ('approve', 'reject'):
            return [IsAuthenticated(), HasPromotionApprove()]
        if self.action == 'cancel':
            return [IsAuthenticated(), HasPromotionCancel()]
        return [IsAuthenticated(), HasPromotionRead()]

    def get_queryset(self):
        """Apply filters."""
        queryset = filter_activity_queryset(super().get_queryset(), self.request)
        return _filter_platform_promotion_list(
            queryset, self.request, reviewing_status=SeckillActivity.STATUS_REVIEWING,
        )

    def list(self, request: Request, *args, **kwargs) -> Response:
        return list_response(self, request, self.get_queryset())

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return success_response(data=self.get_serializer(self.get_object()).data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        return create_response(
            self, self.get_serializer(data=request.data), request.user, SeckillActivity.STATUS_PENDING,
        )

    def update(self, request: Request, *args, **kwargs) -> Response:
        if not user_has_permission(request.user, 'promotion:update'):
            return error_response('无编辑权限')
        return update_response(self, self.get_object(), request, EDITABLE_APPROVAL_STATUSES, **kwargs)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        if instance.status not in {SeckillActivity.STATUS_PENDING, SeckillActivity.STATUS_CANCELLED}:
            return error_response('仅待审核或已取消的活动可删除')
        if not user_has_permission(request.user, 'promotion:cancel'):
            return error_response('无删除权限')
        instance.delete()
        return success_response(message='删除成功')

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request: Request, pk: int | None = None) -> Response:
        activity = self.get_object()
        if activity.status != SeckillActivity.STATUS_PENDING:
            return error_response('仅待审核的活动可提交')
        activity.status = SeckillActivity.STATUS_REVIEWING
        activity.reject_reason = ''
        activity.save(update_fields=['status', 'reject_reason', 'updated_at'])
        return success_response(data=self.get_serializer(activity).data, message='已提交审核')

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request: Request, pk: int | None = None) -> Response:
        activity = self.get_object()
        if activity.status != SeckillActivity.STATUS_REVIEWING:
            return error_response('仅审核中的活动可审批')
        now = timezone.now()
        activity.status = SeckillActivity.STATUS_RUNNING
        activity.approved_by = request.user
        activity.approved_at = now
        activity.reject_reason = ''
        activity.save(update_fields=['status', 'approved_by', 'approved_at', 'reject_reason', 'updated_at'])
        if now > activity.end_time:
            activity.status = SeckillActivity.STATUS_ENDED
            activity.save(update_fields=['status', 'updated_at'])
        return success_response(data=self.get_serializer(activity).data, message='审批通过')

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request: Request, pk: int | None = None) -> Response:
        activity = self.get_object()
        if activity.status != SeckillActivity.STATUS_REVIEWING:
            return error_response('仅审核中的活动可驳回')
        reason = request.data.get('reason', '').strip()
        if not reason:
            return error_response('请填写驳回原因')
        activity.status = SeckillActivity.STATUS_PENDING
        activity.reject_reason = reason
        activity.approved_by = request.user
        activity.approved_at = timezone.now()
        activity.save(update_fields=['status', 'reject_reason', 'approved_by', 'approved_at', 'updated_at'])
        return success_response(data=self.get_serializer(activity).data, message='已驳回')

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request: Request, pk: int | None = None) -> Response:
        activity = self.get_object()
        if activity.status in {SeckillActivity.STATUS_ENDED, SeckillActivity.STATUS_CANCELLED}:
            return error_response('活动已结束或已取消')
        activity.status = SeckillActivity.STATUS_CANCELLED
        activity.save(update_fields=['status', 'updated_at'])
        return success_response(data=self.get_serializer(activity).data, message='活动已终止')


class GroupBuyActivityViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """Group buy activity CRUD with approval workflow."""

    queryset = GroupBuyActivity.objects.select_related('product', 'created_by', 'approved_by').all()
    serializer_class = GroupBuyActivitySerializer
    pagination_class = StandardPagination

    def get_permissions(self):
        """Action-based permissions."""
        if self.action in ('list', 'retrieve', 'group_orders'):
            return [IsAuthenticated(), HasPromotionRead()]
        if self.action == 'create':
            return [IsAuthenticated(), HasPromotionCreate()]
        if self.action in ('update', 'partial_update'):
            return [IsAuthenticated(), HasPromotionUpdate()]
        if self.action == 'destroy':
            return [IsAuthenticated(), HasPromotionCancel()]
        if self.action == 'submit':
            return [IsAuthenticated(), HasPromotionSubmit()]
        if self.action in ('approve', 'reject'):
            return [IsAuthenticated(), HasPromotionApprove()]
        if self.action == 'cancel':
            return [IsAuthenticated(), HasPromotionCancel()]
        return [IsAuthenticated(), HasPromotionRead()]

    def get_queryset(self):
        """Apply filters."""
        queryset = filter_activity_queryset(super().get_queryset(), self.request)
        return _filter_platform_promotion_list(
            queryset, self.request, reviewing_status=GroupBuyActivity.STATUS_REVIEWING,
        )

    def list(self, request: Request, *args, **kwargs) -> Response:
        return list_response(self, request, self.get_queryset())

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return success_response(data=self.get_serializer(self.get_object()).data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        return create_response(
            self, self.get_serializer(data=request.data), request.user, GroupBuyActivity.STATUS_PENDING,
        )

    def update(self, request: Request, *args, **kwargs) -> Response:
        if not user_has_permission(request.user, 'promotion:update'):
            return error_response('无编辑权限')
        return update_response(self, self.get_object(), request, EDITABLE_APPROVAL_STATUSES, **kwargs)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        if instance.status not in {GroupBuyActivity.STATUS_PENDING, GroupBuyActivity.STATUS_CANCELLED}:
            return error_response('仅待审核或已取消的活动可删除')
        if not user_has_permission(request.user, 'promotion:cancel'):
            return error_response('无删除权限')
        instance.delete()
        return success_response(message='删除成功')

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request: Request, pk: int | None = None) -> Response:
        activity = self.get_object()
        if activity.status != GroupBuyActivity.STATUS_PENDING:
            return error_response('仅待审核的活动可提交')
        activity.status = GroupBuyActivity.STATUS_REVIEWING
        activity.reject_reason = ''
        activity.save(update_fields=['status', 'reject_reason', 'updated_at'])
        return success_response(data=self.get_serializer(activity).data, message='已提交审核')

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request: Request, pk: int | None = None) -> Response:
        activity = self.get_object()
        if activity.status != GroupBuyActivity.STATUS_REVIEWING:
            return error_response('仅审核中的活动可审批')
        now = timezone.now()
        activity.status = GroupBuyActivity.STATUS_RUNNING
        activity.approved_by = request.user
        activity.approved_at = now
        activity.reject_reason = ''
        activity.save(update_fields=['status', 'approved_by', 'approved_at', 'reject_reason', 'updated_at'])
        if now > activity.end_time:
            activity.status = GroupBuyActivity.STATUS_ENDED
            activity.save(update_fields=['status', 'updated_at'])
        return success_response(data=self.get_serializer(activity).data, message='审批通过')

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request: Request, pk: int | None = None) -> Response:
        activity = self.get_object()
        if activity.status != GroupBuyActivity.STATUS_REVIEWING:
            return error_response('仅审核中的活动可驳回')
        reason = request.data.get('reason', '').strip()
        if not reason:
            return error_response('请填写驳回原因')
        activity.status = GroupBuyActivity.STATUS_PENDING
        activity.reject_reason = reason
        activity.approved_by = request.user
        activity.approved_at = timezone.now()
        activity.save(update_fields=['status', 'reject_reason', 'approved_by', 'approved_at', 'updated_at'])
        return success_response(data=self.get_serializer(activity).data, message='已驳回')

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request: Request, pk: int | None = None) -> Response:
        activity = self.get_object()
        if activity.status in {GroupBuyActivity.STATUS_ENDED, GroupBuyActivity.STATUS_CANCELLED}:
            return error_response('活动已结束或已取消')
        activity.status = GroupBuyActivity.STATUS_CANCELLED
        activity.save(update_fields=['status', 'updated_at'])
        return success_response(data=self.get_serializer(activity).data, message='活动已终止')

    @action(detail=True, methods=['get'], url_path='group-orders')
    def group_orders(self, request: Request, pk: int | None = None) -> Response:
        """List group orders for activity."""
        activity = self.get_object()
        queryset = GroupOrder.objects.filter(activity=activity).select_related(
            'order', 'captain', 'activity',
        )
        page = self.paginate_queryset(queryset)
        serializer = GroupOrderSerializer(page if page is not None else queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return success_response(data=serializer.data)


class CouponViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    """Coupon CRUD with publish/disable workflow."""

    queryset = Coupon.objects.prefetch_related('applicable_products').select_related(
        'applicable_category', 'created_by',
    ).all()
    serializer_class = CouponSerializer
    pagination_class = StandardPagination

    def get_permissions(self):
        """Action-based permissions."""
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated(), HasCouponRead()]
        if self.action == 'create':
            return [IsAuthenticated(), HasCouponCreate()]
        if self.action in ('update', 'partial_update'):
            return [IsAuthenticated(), HasCouponUpdate()]
        if self.action == 'destroy':
            return [IsAuthenticated(), HasCouponUpdate()]
        if self.action in ('publish', 'disable'):
            return [IsAuthenticated(), HasCouponPublish()]
        return [IsAuthenticated(), HasCouponRead()]

    def get_queryset(self):
        """Apply filters."""
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        keyword = self.request.query_params.get('keyword')
        coupon_type = self.request.query_params.get('coupon_type')
        if status_param:
            queryset = queryset.filter(status=status_param)
        if keyword:
            queryset = queryset.filter(name__icontains=keyword)
        if coupon_type:
            queryset = queryset.filter(coupon_type=coupon_type)
        return _filter_platform_coupon_list(queryset, self.request)

    def list(self, request: Request, *args, **kwargs) -> Response:
        return list_response(self, request, self.get_queryset())

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return success_response(data=self.get_serializer(self.get_object()).data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer_error_message(serializer))
        try:
            instance = serializer.save(created_by=request.user, status=Coupon.STATUS_DRAFT)
        except Exception:
            logger.exception('Create coupon failed')
            return error_response('创建失败', code=50000, http_status=500)
        return success_response(
            data=self.get_serializer(instance).data,
            message='创建成功',
            http_status=status.HTTP_201_CREATED,
        )

    def update(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        if instance.status not in {Coupon.STATUS_DRAFT, Coupon.STATUS_DISABLED}:
            return error_response('仅草稿或已停用的优惠券可编辑')
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return error_response(serializer_error_message(serializer))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Update coupon failed')
            return error_response('更新失败', code=50000, http_status=500)
        return success_response(data=self.get_serializer(instance).data, message='更新成功')

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        if instance.status != Coupon.STATUS_DRAFT:
            return error_response('仅草稿状态的优惠券可删除')
        instance.delete()
        return success_response(message='删除成功')

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request: Request, pk: int | None = None) -> Response:
        """Publish coupon."""
        coupon = self.get_object()
        if coupon.status != Coupon.STATUS_DRAFT:
            return error_response('仅草稿状态的优惠券可发布')
        coupon.status = Coupon.STATUS_PUBLISHED
        coupon.save(update_fields=['status', 'updated_at'])
        return success_response(data=self.get_serializer(coupon).data, message='发布成功')

    @action(detail=True, methods=['post'], url_path='disable')
    def disable(self, request: Request, pk: int | None = None) -> Response:
        """Disable coupon."""
        coupon = self.get_object()
        if coupon.status != Coupon.STATUS_PUBLISHED:
            return error_response('仅已发布的优惠券可停用')
        coupon.status = Coupon.STATUS_DISABLED
        coupon.save(update_fields=['status', 'updated_at'])
        return success_response(data=self.get_serializer(coupon).data, message='已停用')


class UserCouponViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """User coupon records (read-only)."""

    queryset = UserCoupon.objects.select_related('coupon', 'user', 'order').all()
    serializer_class = UserCouponSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated, HasCouponRead]

    def get_queryset(self):
        """Filter by coupon."""
        queryset = super().get_queryset()
        coupon_id = self.request.query_params.get('coupon_id')
        status_param = self.request.query_params.get('status')
        if coupon_id:
            queryset = queryset.filter(coupon_id=coupon_id)
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    def list(self, request: Request, *args, **kwargs) -> Response:
        return list_response(self, request, self.get_queryset())

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return success_response(data=self.get_serializer(self.get_object()).data)
