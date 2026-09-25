"""Customer feedback views."""

import logging

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination
from common.response import error_response, success_response
from feedback.models import CustomerFeedback
from feedback.permissions import HasFeedbackDelete, HasFeedbackRead, HasFeedbackReply
from feedback.serializers import (
    CustomerFeedbackReplySerializer,
    CustomerFeedbackSerializer,
    CustomerFeedbackSubmitSerializer,
)
from customers.permissions import IsCustomerAuthenticated

logger = logging.getLogger(__name__)


class CustomerFeedbackViewSet(viewsets.ModelViewSet):
    """Admin customer feedback viewset."""

    queryset = CustomerFeedback.objects.select_related('customer', 'handler').all()
    serializer_class = CustomerFeedbackSerializer
    pagination_class = StandardPagination
    http_method_names = ['get', 'delete', 'head', 'options', 'post']

    def get_permissions(self):
        """Permission by action."""
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated(), HasFeedbackRead()]
        if self.action in ('reply',):
            return [IsAuthenticated(), HasFeedbackReply()]
        if self.action == 'destroy':
            return [IsAuthenticated(), HasFeedbackDelete()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filter feedback list."""
        queryset = super().get_queryset()
        feedback_type = self.request.query_params.get('feedback_type')
        status_param = self.request.query_params.get('status')
        keyword = self.request.query_params.get('keyword')
        if feedback_type:
            queryset = queryset.filter(feedback_type=feedback_type)
        if status_param:
            queryset = queryset.filter(status=status_param)
        if keyword:
            queryset = queryset.filter(nickname__icontains=keyword) | queryset.filter(
                phone__icontains=keyword,
            )
        return queryset

    def list(self, request: Request, *args, **kwargs) -> Response:
        """List feedback entries."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        """Retrieve feedback detail."""
        return success_response(data=self.get_serializer(self.get_object()).data)

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Delete feedback (super admin only)."""
        try:
            self.get_object().delete()
        except Exception:
            logger.exception('Delete feedback failed')
            return error_response('删除失败', code=50000, http_status=500)
        return success_response(message='删除成功')

    @action(detail=True, methods=['post'], url_path='reply')
    def reply(self, request: Request, pk: int | None = None) -> Response:
        """Reply to feedback and update status."""
        instance = self.get_object()
        serializer = CustomerFeedbackReplySerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance.status = serializer.validated_data['status']
            instance.handler_remark = serializer.validated_data.get('handler_remark', '')
            instance.handler = request.user
            instance.handled_at = timezone.now()
            instance.save(
                update_fields=['status', 'handler_remark', 'handler', 'handled_at'],
            )
            if instance.handler_remark and instance.customer_id:
                from notification.services import notify_feedback_reply

                notify_feedback_reply(feedback=instance)
        except Exception:
            logger.exception('Reply feedback failed')
            return error_response('回复失败', code=50000, http_status=500)
        return success_response(
            data=CustomerFeedbackSerializer(instance).data,
            message='回复成功',
        )


class FeedbackSubmitView(APIView):
    """Public endpoint for mall customers to submit feedback."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Create a feedback entry from storefront."""
        serializer = CustomerFeedbackSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Submit feedback failed')
            return error_response('提交失败', code=50000, http_status=500)
        return success_response(
            data=CustomerFeedbackSerializer(instance).data,
            message='留言提交成功',
            http_status=status.HTTP_201_CREATED,
        )


class CustomerFeedbackMineView(APIView):
    """Authenticated mall customer feedback list and submit."""

    permission_classes = [IsCustomerAuthenticated]

    def get(self, request: Request) -> Response:
        queryset = CustomerFeedback.objects.filter(customer=request.customer).order_by('-id')
        feedback_type = request.query_params.get('feedback_type')
        if feedback_type:
            queryset = queryset.filter(feedback_type=feedback_type)
        serializer = CustomerFeedbackSerializer(queryset[:50], many=True)
        return success_response(data=serializer.data)

    def post(self, request: Request) -> Response:
        customer = request.customer
        payload = {
            **request.data,
            'nickname': customer.display_name,
            'phone': customer.phone or '',
        }
        if request.data.get('tenant_id') is not None:
            payload['tenant_id'] = request.data.get('tenant_id')
        serializer = CustomerFeedbackSubmitSerializer(data=payload, context={'customer': customer})
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
            if instance.customer_id != customer.id:
                instance.customer = customer
                instance.save(update_fields=['customer'])
        except Exception:
            logger.exception('Submit customer feedback failed')
            return error_response('提交失败', code=50000, http_status=500)
        return success_response(
            data=CustomerFeedbackSerializer(instance).data,
            message='提交成功',
            http_status=status.HTTP_201_CREATED,
        )
