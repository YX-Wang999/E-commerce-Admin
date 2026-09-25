"""Customer-facing membership API."""

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination
from common.response import error_response, success_response
from customers.permissions import IsCustomerAuthenticated
from customers.utils import get_request_customer
from membership.models import GrowthLog, MemberLevel
from membership.serializers import GrowthLogSerializer, MemberLevelSerializer
from membership.services import build_profile_payload, check_level_upgrade, checkin, get_or_create_profile


class MembershipLevelsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        levels = MemberLevel.objects.filter(is_active=True).order_by('level')
        return success_response(data=MemberLevelSerializer(levels, many=True).data)


class MembershipMyProfileView(APIView):
    permission_classes = [IsAuthenticated, IsCustomerAuthenticated]

    def get(self, request: Request) -> Response:
        customer = get_request_customer(request)
        if customer is None:
            return error_response('请先登录', http_status=401)
        return success_response(data=build_profile_payload(customer))


class MembershipGrowthLogsView(APIView):
    permission_classes = [IsAuthenticated, IsCustomerAuthenticated]

    def get(self, request: Request) -> Response:
        customer = get_request_customer(request)
        if customer is None:
            return error_response('请先登录', http_status=401)
        queryset = GrowthLog.objects.filter(customer=customer).order_by('-id')
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = GrowthLogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class MembershipCheckinView(APIView):
    permission_classes = [IsAuthenticated, IsCustomerAuthenticated]

    def post(self, request: Request) -> Response:
        customer = get_request_customer(request)
        if customer is None:
            return error_response('请先登录', http_status=401)
        result = checkin(customer)
        if result['code'] != 0:
            return error_response(result['message'])
        payload = build_profile_payload(customer)
        payload['growth_gained'] = result.get('growth_points', 0)
        return success_response(data=payload, message=result['message'])


class MembershipLevelUpView(APIView):
    permission_classes = [IsAuthenticated, IsCustomerAuthenticated]

    def post(self, request: Request) -> Response:
        customer = get_request_customer(request)
        if customer is None:
            return error_response('请先登录', http_status=401)
        get_or_create_profile(customer)
        upgraded = check_level_upgrade(customer)
        payload = build_profile_payload(customer)
        message = '升级成功' if upgraded else '暂未满足升级条件'
        return success_response(data={'upgraded': upgraded, 'profile': payload}, message=message)
