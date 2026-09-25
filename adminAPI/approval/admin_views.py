"""Platform approval workbench APIs."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from approval.models import Approval
from approval.serializers import ApprovalDetailSerializer, ApprovalSerializer
from approval.services import approve_record, get_pending_summary, reject_record
from common.pagination import StandardPagination
from common.response import error_response, success_response
from tenants.permissions import user_has_permission


def _can_review(user) -> bool:
    if user.is_superuser:
        return True
    return user_has_permission(user, 'tenant:approve') or user_has_permission(user, 'promotion:approve')


class ApprovalSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        if not _can_review(request.user):
            return error_response('无权查看审核工作台', http_status=403)
        pending_total = Approval.objects.filter(status=Approval.STATUS_PENDING).count()
        return success_response(
            data={
                'pending_total': pending_total,
                'groups': get_pending_summary(),
            },
        )


class ApprovalListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        if not _can_review(request.user):
            return error_response('无权查看审核工作台', http_status=403)
        queryset = Approval.objects.select_related('reviewer').order_by('-created_at')
        status_value = (request.query_params.get('status') or Approval.STATUS_PENDING).strip()
        if status_value:
            queryset = queryset.filter(status=status_value)
        approval_type = (request.query_params.get('approval_type') or '').strip()
        if approval_type:
            queryset = queryset.filter(approval_type=approval_type)
        keyword = (request.query_params.get('keyword') or '').strip()
        if keyword:
            queryset = queryset.filter(title__icontains=keyword)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = ApprovalSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ApprovalDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, pk: int) -> Response:
        if not _can_review(request.user):
            return error_response('无权查看审核详情', http_status=403)
        approval = Approval.objects.select_related('reviewer').prefetch_related('logs').filter(pk=pk).first()
        if approval is None:
            return error_response('审核单不存在', http_status=404)
        return success_response(data=ApprovalDetailSerializer(approval).data)


class ApprovalApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        if not _can_review(request.user):
            return error_response('无权审核', http_status=403)
        approval = Approval.objects.filter(pk=pk).first()
        if approval is None:
            return error_response('审核单不存在', http_status=404)
        try:
            approval = approve_record(approval, request.user, **request.data)
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(data=ApprovalDetailSerializer(approval).data, message='审核通过')


class ApprovalRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        if not _can_review(request.user):
            return error_response('无权审核', http_status=403)
        approval = Approval.objects.filter(pk=pk).first()
        if approval is None:
            return error_response('审核单不存在', http_status=404)
        reason = (request.data.get('reject_reason') or '').strip()
        try:
            approval = reject_record(approval, request.user, reject_reason=reason, **request.data)
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(data=ApprovalDetailSerializer(approval).data, message='已驳回')


class ApprovalBatchApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        if not _can_review(request.user):
            return error_response('无权审核', http_status=403)
        ids = request.data.get('ids') or []
        if not isinstance(ids, list) or not ids:
            return error_response('请选择审核单')
        success_count = 0
        errors: list[str] = []
        for pk in ids:
            approval = Approval.objects.filter(pk=pk, status=Approval.STATUS_PENDING).first()
            if approval is None:
                continue
            try:
                approve_record(approval, request.user, **request.data)
                success_count += 1
            except ValueError as exc:
                errors.append(f'#{pk}: {exc}')
        return success_response(
            data={'success_count': success_count, 'errors': errors},
            message=f'已处理 {success_count} 条',
        )
