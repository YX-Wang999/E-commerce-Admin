"""Seller complaint API views."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import Complaint
from common.pagination import StandardPagination
from common.response import error_response, success_response
from complaints.permissions import IsTenantComplaintStaff
from complaints.serializers import ComplaintSerializer, MerchantReplySerializer
from complaints.services import merchant_reply_complaint
from tenants.seller_permissions import IsTenantStaffMember


class SellerComplaintSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        pending = Complaint.objects.filter(
            tenant=request.tenant,
            status__in=[Complaint.STATUS_PENDING, Complaint.STATUS_MERCHANT_PROCESSING],
        ).count()
        return success_response(data={'pending_count': pending})


class SellerComplaintListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        queryset = Complaint.objects.filter(tenant=request.tenant).select_related(
            'customer',
            'order',
        ).order_by('-id')
        status_param = (request.query_params.get('status') or '').strip()
        if status_param:
            queryset = queryset.filter(status=status_param)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = ComplaintSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)


class SellerComplaintDetailView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request, pk: int) -> Response:
        complaint = Complaint.objects.filter(tenant=request.tenant, pk=pk).select_related(
            'customer',
            'order',
            'reviewed_by',
        ).prefetch_related('messages').first()
        if complaint is None:
            return error_response('投诉不存在', http_status=404)
        return success_response(
            data=ComplaintSerializer(complaint, context={'request': request}).data,
        )


class SellerComplaintReplyView(APIView):
    permission_classes = [IsAuthenticated, IsTenantComplaintStaff]

    def post(self, request: Request, pk: int) -> Response:
        complaint = Complaint.objects.filter(tenant=request.tenant, pk=pk).first()
        if complaint is None:
            return error_response('投诉不存在', http_status=404)
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
