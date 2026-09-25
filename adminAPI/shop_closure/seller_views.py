"""Seller shop closure views."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.response import error_response, success_response
from shop_closure.models import ClosureApplication
from shop_closure.serializers import ClosureApplicationSerializer, ClosureApplySerializer, ClosureConditionSerializer
from shop_closure.services import (
    cancel_closure_application,
    conditions_met,
    create_closure_application,
    evaluate_closure_conditions,
    get_active_closure_application,
    process_due_closures,
)
from tenants.seller_permissions import IsTenantStaffManager


class SellerClosureConditionsView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffManager]

    def get(self, request: Request) -> Response:
        process_due_closures()
        checks = evaluate_closure_conditions(request.tenant)
        serializer = ClosureConditionSerializer(checks, many=True)
        _, _ = conditions_met(request.tenant)
        return success_response(
            data={
                'checks': serializer.data,
                'all_passed': all(item['is_completed'] for item in checks),
            },
        )


class SellerClosureApplicationView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffManager]

    def get(self, request: Request) -> Response:
        process_due_closures()
        application = (
            ClosureApplication.objects.filter(tenant=request.tenant)
            .prefetch_related('checklist')
            .order_by('-id')
            .first()
        )
        if application is None:
            return success_response(data=None)
        return success_response(data=ClosureApplicationSerializer(application).data)

    def post(self, request: Request) -> Response:
        serializer = ClosureApplySerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            application = create_closure_application(
                request.tenant,
                reason=serializer.validated_data['reason'],
                detail=serializer.validated_data.get('detail', ''),
                attachments=serializer.validated_data.get('attachments') or [],
            )
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(
            data=ClosureApplicationSerializer(application).data,
            message='注销申请已提交',
        )

    def delete(self, request: Request) -> Response:
        application = get_active_closure_application(request.tenant)
        if application is None:
            return error_response('没有可撤回的申请')
        try:
            cancel_closure_application(application)
        except ValueError as exc:
            return error_response(str(exc))
        return success_response(message='已撤回注销申请')
