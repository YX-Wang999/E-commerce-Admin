"""Platform shop closure admin views."""

from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination
from common.response import error_response, success_response
from shop_closure.models import ClosureApplication
from shop_closure.serializers import ClosureApplicationSerializer, ClosureReviewSerializer
from shop_closure.services import (
    approve_closure_application,
    execute_closure,
    process_due_closures,
    reject_closure_application,
)
from tenants.permissions import user_has_permission


def _can_view_closure(user) -> bool:
    if user.is_superuser:
        return True
    return user_has_permission(user, 'tenant:view')


def _can_review_closure(user) -> bool:
    if user.is_superuser:
        return True
    return user_has_permission(user, 'tenant:approve')


class AdminClosureListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        if not _can_view_closure(request.user):
            return error_response('无权查看注销申请', http_status=403)
        process_due_closures()
        queryset = ClosureApplication.objects.select_related('tenant', 'reviewed_by').prefetch_related('checklist')
        status = request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        keyword = (request.query_params.get('keyword') or '').strip()
        if keyword:
            queryset = queryset.filter(tenant__name__icontains=keyword)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset.order_by('-id'), request)
        serializer = ClosureApplicationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminClosureDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, pk: int) -> Response:
        if not _can_view_closure(request.user):
            return error_response('无权查看注销申请', http_status=403)
        application = (
            ClosureApplication.objects.select_related('tenant', 'reviewed_by')
            .prefetch_related('checklist', 'notifications')
            .filter(pk=pk)
            .first()
        )
        if application is None:
            return error_response('申请不存在', http_status=404)
        data = ClosureApplicationSerializer(application).data
        data['notifications'] = [
            {
                'id': item.id,
                'recipient': item.recipient,
                'channel': item.channel,
                'content': item.content,
                'sent_at': item.sent_at,
                'is_delivered': item.is_delivered,
            }
            for item in application.notifications.all()
        ]
        return success_response(data=data)


class AdminClosureApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        if not _can_review_closure(request.user):
            return error_response('无权审核注销申请', http_status=403)
        application = ClosureApplication.objects.filter(pk=pk).first()
        if application is None:
            return error_response('申请不存在', http_status=404)
        serializer = ClosureReviewSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            application = approve_closure_application(
                application,
                request.user,
                notice_days=serializer.validated_data.get('notice_days'),
            )
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(data=ClosureApplicationSerializer(application).data, message='已通过，进入公示期')


class AdminClosureRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        if not _can_review_closure(request.user):
            return error_response('无权审核注销申请', http_status=403)
        application = ClosureApplication.objects.filter(pk=pk).first()
        if application is None:
            return error_response('申请不存在', http_status=404)
        serializer = ClosureReviewSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        reason = serializer.validated_data.get('reject_reason', '').strip()
        if not reason:
            return error_response('请填写驳回原因')
        try:
            application = reject_closure_application(application, request.user, reject_reason=reason)
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(data=ClosureApplicationSerializer(application).data, message='已驳回')


class AdminClosureCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        if not _can_review_closure(request.user):
            return error_response('无权执行注销', http_status=403)
        application = ClosureApplication.objects.filter(pk=pk).first()
        if application is None:
            return error_response('申请不存在', http_status=404)
        try:
            application = execute_closure(application, operator=request.user)
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(data=ClosureApplicationSerializer(application).data, message='店铺已正式注销')


class AdminClosureExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        if not _can_view_closure(request.user):
            return error_response('无权导出', http_status=403)
        rows = ClosureApplication.objects.select_related('tenant').order_by('-id')[:5000]
        lines = ['id,tenant,status,reason,created_at,completed_at']
        for item in rows:
            lines.append(
                f'{item.id},{item.tenant.name},{item.status},{item.reason},{item.created_at},{item.completed_at or ""}',
            )
        content = '\n'.join(lines)
        response = HttpResponse(content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="closure_applications.csv"'
        return response
