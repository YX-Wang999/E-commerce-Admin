"""Complaint dispute API views."""

from django.db.models import Case, IntegerField, Q, Value, When
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from chat.models import Complaint
from common.pagination import StandardPagination
from common.response import error_response, success_response
from complaints.permissions import (
    IsCustomerComplaintUser,
    IsCustomerOrStaff,
    IsPlatformComplaintStaff,
    IsTenantComplaintStaff,
    user_is_platform_complaint_staff,
)
from complaints.serializers import (
    ComplaintCreateSerializer,
    ComplaintMessageCreateSerializer,
    ComplaintSerializer,
    CustomerReviewSerializer,
    MerchantReplySerializer,
    PlatformReviewSerializer,
    RequestPlatformSerializer,
)
from complaints.services import (
    add_complaint_message,
    close_complaint,
    create_complaint,
    customer_review_complaint,
    merchant_reply_complaint,
    platform_review_complaint,
    request_platform_intervention,
)
from customers.permissions import IsCustomerAuthenticated


class ComplaintViewSet(viewsets.ViewSet):
    pagination_class = StandardPagination

    def _base_queryset(self):
        return Complaint.objects.select_related(
            'customer',
            'tenant',
            'order',
            'reviewed_by',
        ).prefetch_related('messages')

    def _filter_for_actor(self, request: Request, queryset):
        customer = getattr(request, 'customer', None)
        tenant = getattr(request, 'tenant', None)
        user = getattr(request, 'user', None)
        if customer is not None:
            return queryset.filter(customer=customer)
        if tenant is not None and user and user.is_authenticated:
            return queryset.filter(tenant=tenant)
        return queryset

    def _get_complaint(self, request: Request, pk: int):
        try:
            complaint = self._base_queryset().get(pk=pk)
        except Complaint.DoesNotExist:
            return None, error_response('投诉不存在', http_status=404)
        customer = getattr(request, 'customer', None)
        tenant = getattr(request, 'tenant', None)
        if customer is not None:
            if complaint.customer_id != customer.id:
                return None, error_response('无权查看该投诉', http_status=403)
            return complaint, None
        if tenant is not None:
            if complaint.tenant_id != tenant.id:
                return None, error_response('无权查看该投诉', http_status=403)
            return complaint, None
        if request.user.is_authenticated and user_is_platform_complaint_staff(request.user):
            return complaint, None
        return None, error_response('无权查看该投诉', http_status=403)

    def get_permissions(self):
        if self.action == 'create':
            return [IsCustomerAuthenticated()]
        if self.action in ('list', 'retrieve', 'send_message'):
            return [IsCustomerOrStaff()]
        if self.action in ('customer_review', 'request_platform'):
            return [IsCustomerAuthenticated()]
        if self.action in ('merchant_reply',):
            return [IsAuthenticated(), IsTenantComplaintStaff()]
        if self.action in ('platform_review', 'close'):
            return [IsAuthenticated(), IsPlatformComplaintStaff()]
        return [IsAuthenticated()]

    def list(self, request: Request) -> Response:
        customer = getattr(request, 'customer', None)
        tenant = getattr(request, 'tenant', None)
        if customer is None and tenant is None and not user_is_platform_complaint_staff(request.user):
            return error_response('无权访问', http_status=403)

        queryset = self._filter_for_actor(request, self._base_queryset())
        status_param = (request.query_params.get('status') or '').strip()
        category = (request.query_params.get('category') or '').strip()
        tenant_id = (request.query_params.get('tenant_id') or '').strip()
        keyword = (request.query_params.get('keyword') or '').strip()
        if status_param:
            queryset = queryset.filter(status=status_param)
        if category:
            queryset = queryset.filter(category=category)
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword)
                | Q(content__icontains=keyword)
                | Q(order__order_no__icontains=keyword)
                | Q(customer__phone__icontains=keyword),
            )
        if (
            customer is None
            and tenant is None
            and user_is_platform_complaint_staff(request.user)
        ):
            show_all = (request.query_params.get('all') or '').strip().lower() in ('1', 'true', 'yes')
            if not show_all and not status_param:
                queryset = queryset.filter(status=Complaint.STATUS_PLATFORM_REVIEWING)
        queryset = queryset.annotate(
            status_order=Case(
                When(status=Complaint.STATUS_PENDING, then=Value(0)),
                When(status=Complaint.STATUS_PLATFORM_REVIEWING, then=Value(1)),
                When(status=Complaint.STATUS_MERCHANT_PROCESSING, then=Value(2)),
                When(status=Complaint.STATUS_CUSTOMER_REVIEW, then=Value(3)),
                default=Value(4),
                output_field=IntegerField(),
            ),
        ).order_by('status_order', '-id')
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = ComplaintSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    def retrieve(self, request: Request, pk=None) -> Response:
        complaint, err = self._get_complaint(request, int(pk))
        if err:
            return err
        return success_response(
            data=ComplaintSerializer(complaint, context={'request': request}).data,
        )

    def create(self, request: Request) -> Response:
        serializer = ComplaintCreateSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message))
        data = serializer.validated_data
        try:
            complaint = create_complaint(
                customer=request.customer,
                tenant_id=data['tenant_id'],
                order_id=data['order_id'],
                category=data['category'],
                title=data['title'],
                content=data['content'],
                attachments=data.get('attachments') or [],
            )
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(
            data=ComplaintSerializer(complaint, context={'request': request}).data,
            message='投诉已提交，商户将尽快处理',
            http_status=201,
        )

    @action(detail=True, methods=['post'], url_path='messages')
    def send_message(self, request: Request, pk=None) -> Response:
        complaint, err = self._get_complaint(request, int(pk))
        if err:
            return err
        serializer = ComplaintMessageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message))
        data = serializer.validated_data
        customer = getattr(request, 'customer', None)
        tenant = getattr(request, 'tenant', None)
        try:
            if customer is not None:
                if complaint.customer_id != customer.id:
                    return error_response('无权操作', http_status=403)
                message = add_complaint_message(
                    complaint=complaint,
                    sender_type='customer',
                    sender_id=customer.id,
                    content=data['content'],
                    attachments=data.get('attachments'),
                )
            elif tenant is not None:
                message = add_complaint_message(
                    complaint=complaint,
                    sender_type='merchant',
                    sender_id=tenant.id,
                    content=data['content'],
                    attachments=data.get('attachments'),
                )
            else:
                from complaints.permissions import user_is_platform_complaint_staff

                if not user_is_platform_complaint_staff(request.user):
                    return error_response('无权操作', http_status=403)
                message = add_complaint_message(
                    complaint=complaint,
                    sender_type='platform',
                    sender_id=request.user.id,
                    content=data['content'],
                    attachments=data.get('attachments'),
                    is_internal=data.get('is_internal', False),
                )
        except ValueError as exc:
            return error_response(str(exc))
        complaint.refresh_from_db()
        return success_response(
            data=ComplaintSerializer(complaint, context={'request': request}).data,
            message='发送成功',
        )

    @action(detail=True, methods=['post'], url_path='merchant-reply')
    def merchant_reply(self, request: Request, pk=None) -> Response:
        complaint, err = self._get_complaint(request, int(pk))
        if err:
            return err
        serializer = MerchantReplySerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message))
        data = serializer.validated_data
        try:
            complaint = merchant_reply_complaint(
                complaint=complaint,
                tenant_id=request.tenant.id,
                content=data['content'],
                attachments=data.get('attachments'),
                mark_processed=data.get('mark_processed', False),
            )
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(
            data=ComplaintSerializer(complaint, context={'request': request}).data,
            message='回复成功',
        )

    @action(detail=True, methods=['post'], url_path='customer-review')
    def customer_review(self, request: Request, pk=None) -> Response:
        complaint, err = self._get_complaint(request, int(pk))
        if err:
            return err
        serializer = CustomerReviewSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message))
        data = serializer.validated_data
        try:
            complaint = customer_review_complaint(
                complaint=complaint,
                customer_id=request.customer.id,
                satisfied=data['satisfied'],
                comment=data.get('comment') or '',
            )
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(
            data=ComplaintSerializer(complaint, context={'request': request}).data,
            message='已提交确认',
        )

    @action(detail=True, methods=['post'], url_path='request-platform')
    def request_platform(self, request: Request, pk=None) -> Response:
        complaint, err = self._get_complaint(request, int(pk))
        if err:
            return err
        serializer = RequestPlatformSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message))
        try:
            complaint = request_platform_intervention(
                complaint=complaint,
                customer_id=request.customer.id,
                reason=serializer.validated_data.get('reason') or '',
            )
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(
            data=ComplaintSerializer(complaint, context={'request': request}).data,
            message='已申请平台介入',
        )

    @action(detail=True, methods=['post'], url_path='platform-review')
    def platform_review(self, request: Request, pk=None) -> Response:
        complaint, err = self._get_complaint(request, int(pk))
        if err:
            return err
        serializer = PlatformReviewSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message))
        data = serializer.validated_data
        try:
            complaint = platform_review_complaint(
                complaint=complaint,
                reviewer=request.user,
                decision=data['decision'],
                platform_remark=data['platform_remark'],
                resolution=data.get('resolution') or '',
                internal_note=data.get('internal_note') or '',
            )
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(
            data=ComplaintSerializer(complaint, context={'request': request}).data,
            message='仲裁完成',
        )

    @action(detail=True, methods=['post'], url_path='close')
    def close(self, request: Request, pk=None) -> Response:
        complaint, err = self._get_complaint(request, int(pk))
        if err:
            return err
        try:
            complaint = close_complaint(complaint=complaint)
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(
            data=ComplaintSerializer(complaint, context={'request': request}).data,
            message='投诉已关闭',
        )
