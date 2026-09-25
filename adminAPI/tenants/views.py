"""Tenant API views."""

import logging

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from chat.models import Conversation
from common.pagination import StandardPagination
from common.response import error_response, success_response
from customers.models import Customer
from orders.models import Order
from products.models import Product
from tenants.models import Tenant, TenantActionLog, TenantStaff, TenantSuspensionLog, TenantChangeLog
from tenants.permissions import (
    HasTenantApprove,
    HasTenantCreate,
    HasTenantDelete,
    HasTenantSuspend,
    HasTenantView,
    HasTenantChangeReview,
    HasTenantChangeView,
)
from tenants.serializers import (
    PublicTenantSerializer,
    TenantDetailSerializer,
    TenantSerializer,
    TenantStaffSerializer,
    TenantSuspensionLogSerializer,
    TenantChangeLogSerializer,
    TenantChangeReviewSerializer,
)
from tenants.services import log_suspension_action
from tenants.utils import delete_tenant_with_staff_users
from tenants.validators import check_tenant_availability

logger = logging.getLogger(__name__)
User = get_user_model()


def _activate_tenant_owner(tenant: Tenant) -> None:
    """Enable owner account after tenant approval."""
    staff = TenantStaff.objects.filter(
        tenant=tenant,
        role=TenantStaff.ROLE_OWNER,
    ).select_related('user').first()
    if staff is None:
        return
    if not staff.is_active:
        staff.is_active = True
        staff.save(update_fields=['is_active'])
    if staff.user_id and not staff.user.is_active:
        User.objects.filter(pk=staff.user_id).update(is_active=True)


def _integrity_error_message(exc: IntegrityError) -> str:
    message = str(exc)
    if 'code' in message:
        return '商户编码已存在，请更换'
    if 'contact_phone' in message:
        return '该联系电话已被其他商户使用，请检查'
    return '数据冲突，请检查后重试'


def _log_tenant_action(tenant: Tenant, *, action: str, operator, remark: str = '') -> None:
    TenantActionLog.objects.create(
        tenant=tenant,
        action=action,
        operator=operator,
        remark=remark,
    )


def _tenant_stats(tenant: Tenant) -> dict:
    from tenants.dashboard_stats import compute_tenant_stats

    return compute_tenant_stats(tenant)


class TenantViewSet(viewsets.ModelViewSet):
    """Platform tenant management."""

    queryset = Tenant.objects.select_related('department', 'approved_by').all()
    serializer_class = TenantSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated, HasTenantView]

    def _is_admin_user(self) -> bool:
        user = self.request.user
        return user.is_authenticated and hasattr(user, 'roles')

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve') and not self._is_admin_user():
            return PublicTenantSerializer
        if self.action == 'retrieve':
            return TenantDetailSerializer
        return TenantSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve') and not self._is_admin_user():
            return [AllowAny()]
        if self.action == 'create':
            return [IsAuthenticated(), HasTenantCreate()]
        if self.action == 'destroy':
            return [IsAuthenticated(), HasTenantDelete()]
        if self.action in ('approve',):
            return [IsAuthenticated(), HasTenantApprove()]
        if self.action in ('suspend', 'resume', 'close'):
            return [IsAuthenticated(), HasTenantSuspend()]
        return [IsAuthenticated(), HasTenantView()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ('list', 'retrieve') and not self._is_admin_user():
            queryset = queryset.filter(status=Tenant.STATUS_ACTIVE, is_active=True)
            code = (self.request.query_params.get('code') or '').strip()
            if code:
                queryset = queryset.filter(code=code)
            return queryset
        if self.action == 'retrieve':
            return queryset.prefetch_related('action_logs__operator', 'suspension_logs__operator')
        # status/keyword 仅用于商户列表筛选，不能影响详情/变更记录等子资源
        if self.action not in ('list', 'summary'):
            return queryset
        keyword = (self.request.query_params.get('keyword') or '').strip()
        status = (self.request.query_params.get('status') or '').strip()
        if keyword:
            queryset = queryset.filter(
                Q(name__icontains=keyword)
                | Q(code__icontains=keyword)
                | Q(contact_name__icontains=keyword)
                | Q(contact_phone__icontains=keyword),
            )
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def perform_create(self, serializer):
        try:
            serializer.save(status=Tenant.STATUS_PENDING)
        except IntegrityError as exc:
            raise ValidationError(_integrity_error_message(exc)) from exc

    def perform_update(self, serializer):
        try:
            serializer.save()
        except IntegrityError as exc:
            raise ValidationError(_integrity_error_message(exc)) from exc

    def list(self, request: Request, *args, **kwargs) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return success_response(data=self.get_serializer(queryset, many=True).data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        data['stats'] = _tenant_stats(instance)
        return success_response(data=data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message))
        try:
            self.perform_create(serializer)
        except ValidationError as exc:
            detail = exc.detail
            if isinstance(detail, list):
                message = str(detail[0])
            elif isinstance(detail, dict):
                first = next(iter(detail.values()))
                message = str(first[0] if isinstance(first, list) else first)
            else:
                message = str(detail)
            return error_response(message)
        instance = serializer.instance
        _log_tenant_action(
            instance,
            action=TenantActionLog.ACTION_CREATE,
            operator=request.user,
            remark='创建商户',
        )
        return success_response(data=self.get_serializer(instance).data, message='创建成功')

    def update(self, request: Request, *args, **kwargs) -> Response:
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message))
        try:
            self.perform_update(serializer)
        except ValidationError as exc:
            detail = exc.detail
            if isinstance(detail, list):
                message = str(detail[0])
            elif isinstance(detail, dict):
                first = next(iter(detail.values()))
                message = str(first[0] if isinstance(first, list) else first)
            else:
                message = str(detail)
            return error_response(message)
        return success_response(data=self.get_serializer(serializer.instance).data, message='更新成功')

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        _log_tenant_action(
            instance,
            action=TenantActionLog.ACTION_DELETE,
            operator=request.user,
            remark=f'删除商户 {instance.name}',
        )
        delete_tenant_with_staff_users(instance)
        return success_response(message='删除成功')

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request: Request) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        return success_response(
            data={
                'total': queryset.count(),
                'pending': queryset.filter(status=Tenant.STATUS_PENDING).count(),
                'active': queryset.filter(status=Tenant.STATUS_ACTIVE).count(),
                'suspended': queryset.filter(status=Tenant.STATUS_SUSPENDED).count(),
                'closed': queryset.filter(status=Tenant.STATUS_CLOSED).count(),
            },
        )

    @action(detail=True, methods=['get'], url_path='stats')
    def stats(self, request: Request, pk: int | None = None) -> Response:
        tenant = self.get_object()
        return success_response(data=_tenant_stats(tenant))

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request: Request, pk: int | None = None) -> Response:
        tenant = self.get_object()
        if tenant.status != Tenant.STATUS_PENDING:
            return error_response('仅待审核商户可审核通过')
        try:
            with transaction.atomic():
                tenant.status = Tenant.STATUS_ACTIVE
                tenant.approved_at = timezone.now()
                tenant.approved_by = request.user
                tenant.is_active = True
                tenant.save(update_fields=['status', 'approved_at', 'approved_by', 'is_active', 'updated_at'])
                _log_tenant_action(
                    tenant,
                    action=TenantActionLog.ACTION_APPROVE,
                    operator=request.user,
                    remark='审核通过',
                )
                _activate_tenant_owner(tenant)
        except Exception:
            logger.exception('Tenant approve failed: tenant_id=%s', tenant.id)
            return error_response('审核失败，请稍后重试', http_status=500)
        serializer = TenantDetailSerializer(tenant, context={'request': request})
        return success_response(data=serializer.data, message='审核通过')

    @action(detail=True, methods=['post'], url_path='suspend')
    def suspend(self, request: Request, pk: int | None = None) -> Response:
        tenant = self.get_object()
        if tenant.status != Tenant.STATUS_ACTIVE:
            return error_response('仅已入驻商户可暂停')
        reason = str(request.data.get('reason', '')).strip()
        if not reason:
            return error_response('请填写暂停原因')
        detail_text = str(request.data.get('detail', '') or request.data.get('detail_text', '')).strip()
        detail_payload = request.data.get('detail_payload') or {}
        if not isinstance(detail_payload, dict):
            detail_payload = {}
        if detail_text:
            detail_payload = {**detail_payload, 'description': detail_text}
        violations = request.data.get('violations') or []
        if violations:
            detail_payload['violations'] = violations
        notify_merchant = bool(request.data.get('notify_merchant', False))

        with transaction.atomic():
            tenant.status = Tenant.STATUS_SUSPENDED
            tenant.is_active = False
            tenant.save(update_fields=['status', 'is_active', 'updated_at'])
            log_suspension_action(
                tenant,
                action=TenantSuspensionLog.ACTION_SUSPEND,
                reason=reason,
                operator=request.user,
                detail=detail_payload,
            )
            _log_tenant_action(
                tenant,
                action=TenantActionLog.ACTION_SUSPEND,
                operator=request.user,
                remark=reason,
            )
        if notify_merchant:
            logger.info('Notify merchant suspend: tenant=%s phone=%s', tenant.id, tenant.contact_phone)
        return success_response(data=self.get_serializer(tenant).data, message='商户已暂停')

    @action(detail=True, methods=['post'], url_path='resume')
    def resume(self, request: Request, pk: int | None = None) -> Response:
        tenant = self.get_object()
        if tenant.status != Tenant.STATUS_SUSPENDED:
            return error_response('仅已暂停商户可恢复')
        reason = str(request.data.get('reason', '')).strip() or '恢复商户'

        with transaction.atomic():
            tenant.status = Tenant.STATUS_ACTIVE
            tenant.is_active = True
            tenant.save(update_fields=['status', 'is_active', 'updated_at'])
            log_suspension_action(
                tenant,
                action=TenantSuspensionLog.ACTION_RESTORE,
                reason=reason,
                operator=request.user,
            )
            _log_tenant_action(
                tenant,
                action=TenantActionLog.ACTION_RESUME,
                operator=request.user,
                remark=reason,
            )
        return success_response(data=self.get_serializer(tenant).data, message='商户已恢复')

    @action(detail=True, methods=['post'], url_path='close')
    def close(self, request: Request, pk: int | None = None) -> Response:
        tenant = self.get_object()
        if tenant.status == Tenant.STATUS_CLOSED:
            return error_response('商户已关闭')
        reason = str(request.data.get('reason', '')).strip()
        if not reason:
            return error_response('请填写关闭原因')
        detail_text = str(request.data.get('detail', '') or request.data.get('detail_text', '')).strip()
        detail_payload = request.data.get('detail_payload') or {}
        if not isinstance(detail_payload, dict):
            detail_payload = {}
        if detail_text:
            detail_payload = {**detail_payload, 'description': detail_text}

        with transaction.atomic():
            tenant.status = Tenant.STATUS_CLOSED
            tenant.is_active = False
            tenant.save(update_fields=['status', 'is_active', 'updated_at'])
            log_suspension_action(
                tenant,
                action=TenantSuspensionLog.ACTION_CLOSE,
                reason=reason,
                operator=request.user,
                detail=detail_payload,
            )
            _log_tenant_action(
                tenant,
                action=TenantActionLog.ACTION_CLOSE,
                operator=request.user,
                remark=reason,
            )
        return success_response(data=self.get_serializer(tenant).data, message='商户已关闭')

    @action(detail=False, methods=['post'], url_path='check')
    def check_availability(self, request: Request) -> Response:
        """Validate tenant fields before save."""
        exclude_id = request.data.get('exclude_id')
        field = (request.data.get('field') or '').strip()
        value = request.data.get('value')

        code = request.data.get('code')
        phone = request.data.get('contact_phone')
        name = request.data.get('name')
        contact_name = request.data.get('contact_name')

        if field and value is not None:
            if field == 'code':
                code = value
            elif field == 'contact_phone':
                phone = value
            elif field == 'name':
                name = value
            elif field == 'contact_name':
                contact_name = value

        result = check_tenant_availability(
            exclude_id=exclude_id,
            code=code,
            phone=phone,
            name=name,
            contact_name=contact_name,
        )
        return success_response(data=result)

    @action(detail=False, methods=['get'], url_path='pending-changes')
    def pending_changes(self, request: Request) -> Response:
        """List all pending profile changes across tenants."""
        if not HasTenantChangeView().has_permission(request, self):
            return error_response('无商户变更查看权限', http_status=403)
        queryset = TenantChangeLog.objects.filter(
            status=TenantChangeLog.STATUS_PENDING,
        ).select_related('tenant', 'operator', 'reviewed_by').order_by('-created_at')
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = TenantChangeLogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=['get'], url_path='change-logs')
    def change_logs(self, request: Request, pk: int | None = None) -> Response:
        """List change logs for a tenant."""
        if not HasTenantChangeView().has_permission(request, self):
            return error_response('无商户变更查看权限', http_status=403)
        tenant = Tenant.objects.filter(pk=pk).first()
        if tenant is None:
            return error_response('商户不存在', http_status=404)
        log_status = (request.query_params.get('status') or '').strip()
        queryset = tenant.change_logs.select_related('operator', 'reviewed_by').all()
        if log_status:
            queryset = queryset.filter(status=log_status)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = TenantChangeLogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        url_path=r'change-logs/(?P<log_id>\d+)/review',
    )
    def review_change(self, request: Request, pk: int | None = None, log_id: int | None = None) -> Response:
        """Approve or reject a pending change."""
        if not HasTenantChangeReview().has_permission(request, self):
            return error_response('无商户变更审核权限', http_status=403)
        tenant = Tenant.objects.filter(pk=pk).first()
        if tenant is None:
            return error_response('商户不存在', http_status=404)
        log = tenant.change_logs.filter(pk=log_id).first()
        if log is None:
            return error_response('变更记录不存在', http_status=404)
        serializer = TenantChangeReviewSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        from tenants.change_services import review_tenant_change

        try:
            log = review_tenant_change(
                log=log,
                reviewer=request.user,
                action=serializer.validated_data['action'],
                remark=serializer.validated_data.get('remark') or '',
            )
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(
            data=TenantChangeLogSerializer(log).data,
            message='审核通过' if log.status == TenantChangeLog.STATUS_APPROVED else '已驳回',
        )


class TenantStaffViewSet(viewsets.ModelViewSet):
    """Tenant staff assignments."""

    queryset = TenantStaff.objects.select_related('tenant', 'user').all()
    serializer_class = TenantStaffSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated, HasTenantView]

    def list(self, request: Request, *args, **kwargs) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        tenant_id = request.query_params.get('tenant')
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return success_response(data=self.get_serializer(queryset, many=True).data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        return success_response(data=self.get_serializer(self.get_object()).data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        instance = serializer.save()
        return success_response(data=self.get_serializer(instance).data, message='创建成功')

    def update(self, request: Request, *args, **kwargs) -> Response:
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        instance = serializer.save()
        return success_response(data=self.get_serializer(instance).data, message='更新成功')

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        self.get_object().delete()
        return success_response(message='删除成功')
