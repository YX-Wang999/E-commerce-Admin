"""Seller customer feedback API."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination
from common.response import error_response, success_response
from feedback.models import CustomerFeedback
from feedback.serializers import CustomerFeedbackReplySerializer, CustomerFeedbackSerializer
from tenants.seller_permissions import IsTenantStaffMember


class SellerFeedbackSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        pending = CustomerFeedback.objects.filter(
            tenant=request.tenant,
            status=CustomerFeedback.STATUS_PENDING,
        ).count()
        return success_response(data={'pending_count': pending})


class SellerFeedbackListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        queryset = CustomerFeedback.objects.filter(tenant=request.tenant).order_by('-id')
        status_param = (request.query_params.get('status') or '').strip()
        feedback_type = (request.query_params.get('feedback_type') or '').strip()
        if status_param:
            queryset = queryset.filter(status=status_param)
        if feedback_type:
            queryset = queryset.filter(feedback_type=feedback_type)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = CustomerFeedbackSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class SellerFeedbackDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request, pk: int) -> Response:
        feedback = CustomerFeedback.objects.filter(tenant=request.tenant, pk=pk).first()
        if feedback is None:
            return error_response('留言不存在', http_status=404)
        return success_response(data=CustomerFeedbackSerializer(feedback).data)


class SellerFeedbackReplyView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def post(self, request: Request, pk: int) -> Response:
        feedback = CustomerFeedback.objects.filter(tenant=request.tenant, pk=pk).first()
        if feedback is None:
            return error_response('留言不存在', http_status=404)
        serializer = CustomerFeedbackReplySerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, list):
                message = message[0]
            return error_response(str(message))
        data = serializer.validated_data
        feedback.status = data['status']
        feedback.handler_remark = (data.get('handler_remark') or '').strip()
        feedback.handler = request.user
        from django.utils import timezone

        feedback.handled_at = timezone.now()
        feedback.save(update_fields=['status', 'handler_remark', 'handler', 'handled_at'])
        if feedback.handler_remark:
            if not feedback.customer_id and feedback.phone:
                from customers.models import Customer

                linked = Customer.objects.filter(phone=feedback.phone, is_active=True).first()
                if linked:
                    feedback.customer = linked
                    feedback.save(update_fields=['customer'])
            from notification.services import notify_feedback_reply

            notify_feedback_reply(feedback=feedback)
        return success_response(
            data=CustomerFeedbackSerializer(feedback).data,
            message='处理成功',
        )
