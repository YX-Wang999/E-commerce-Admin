"""Complaint API views."""

from django.db.models import Case, IntegerField, Q, Value, When
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from chat.complaint_serializers import (
    ComplaintCreateSerializer,
    ComplaintReplySerializer,
    ComplaintSerializer,
)
from chat.models import Complaint
from chat.permissions import HasChatRead, HasChatReply
from chat.services import create_complaint_with_conversation
from common.pagination import StandardPagination
from common.response import error_response, success_response
from customers.permissions import IsCustomerAuthenticated


class ComplaintViewSet(viewsets.ViewSet):
    pagination_class = StandardPagination

    def get_permissions(self):
        if self.action in ('create',):
            return [IsCustomerAuthenticated()]
        if self.action in ('list', 'retrieve', 'reply'):
            return [IsAuthenticated(), HasChatRead()]
        return [IsAuthenticated()]

    def get_reply_permissions(self):
        return [IsAuthenticated(), HasChatReply()]

    def list(self, request: Request) -> Response:
        queryset = Complaint.objects.select_related('customer', 'tenant', 'reviewed_by').all()
        status = (request.query_params.get('status') or '').strip()
        keyword = (request.query_params.get('keyword') or '').strip()
        if status:
            queryset = queryset.filter(status=status)
        if keyword:
            queryset = queryset.filter(
                Q(tenant__name__icontains=keyword)
                | Q(customer__phone__icontains=keyword)
                | Q(content__icontains=keyword),
            )
        queryset = queryset.annotate(
            status_order=Case(
                When(status=Complaint.STATUS_PENDING, then=Value(0)),
                When(status=Complaint.STATUS_PLATFORM_REVIEWING, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            ),
        ).order_by('status_order', '-id')
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = ComplaintSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def retrieve(self, request: Request, pk=None) -> Response:
        try:
            complaint = Complaint.objects.select_related('customer', 'tenant', 'reviewed_by').get(pk=pk)
        except Complaint.DoesNotExist:
            return error_response('投诉不存在', http_status=404)
        return success_response(data=ComplaintSerializer(complaint).data)

    def create(self, request: Request) -> Response:
        serializer = ComplaintCreateSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message))
        from tenants.models import Tenant

        tenant = Tenant.objects.get(pk=serializer.validated_data['tenant_id'])
        complaint, conversation = create_complaint_with_conversation(
            customer=request.customer,
            tenant=tenant,
            category=serializer.validated_data['category'],
            content=serializer.validated_data['content'],
            attachments=serializer.validated_data.get('attachments') or [],
            order_id=serializer.validated_data.get('order'),
        )
        try:
            from complaints.notify import notify_complaint_created

            notify_complaint_created(complaint=complaint)
        except Exception:
            pass
        return success_response(
            data={
                'complaint': ComplaintSerializer(complaint).data,
                'conversation_id': conversation.id,
            },
            message='投诉已提交，商户将尽快处理',
        )

    @action(detail=True, methods=['post'], url_path='reply', permission_classes=[IsAuthenticated, HasChatReply])
    def reply(self, request: Request, pk=None) -> Response:
        try:
            complaint = Complaint.objects.get(pk=pk)
        except Complaint.DoesNotExist:
            return error_response('投诉不存在', http_status=404)
        serializer = ComplaintReplySerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message))
        complaint.platform_reply = serializer.validated_data['platform_reply']
        complaint.status = serializer.validated_data['status']
        complaint.reviewed_by = request.user
        if complaint.status in {Complaint.STATUS_RESOLVED, Complaint.STATUS_REJECTED}:
            complaint.resolved_at = timezone.now()
        complaint.save()
        return success_response(data=ComplaintSerializer(complaint).data, message='处理成功')
