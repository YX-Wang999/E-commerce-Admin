"""Admin membership API."""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination
from common.response import error_response, success_response
from customers.models import Customer
from membership.models import GrowthLog, MemberLevel, MemberProfile
from membership.permissions import HasMembershipManage, HasMembershipRead
from membership.serializers import (
    GrowthLogSerializer,
    MemberLevelSerializer,
    MemberProfileAdminSerializer,
)


class MemberLevelViewSet(viewsets.ModelViewSet):
    queryset = MemberLevel.objects.all().order_by('level')
    serializer_class = MemberLevelSerializer
    pagination_class = StandardPagination

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated(), HasMembershipRead()]
        return [IsAuthenticated(), HasMembershipManage()]


class AdminCustomerMembershipView(APIView):
    permission_classes = [IsAuthenticated, HasMembershipRead]

    def get(self, request: Request, customer_id: int) -> Response:
        customer = Customer.all_objects.filter(pk=customer_id).first()
        if customer is None:
            return error_response('客户不存在', http_status=404)

        from membership.services import build_profile_payload, get_or_create_profile

        profile = get_or_create_profile(customer)
        logs = GrowthLog.objects.filter(customer=customer).order_by('-id')[:50]
        return success_response(
            data={
                'profile': MemberProfileAdminSerializer(profile).data,
                'summary': build_profile_payload(customer),
                'growth_logs': GrowthLogSerializer(logs, many=True).data,
            },
        )
