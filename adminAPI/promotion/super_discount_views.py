"""Super discount API views."""

from __future__ import annotations

from django.db.models import Q
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets

from common.pagination import StandardPagination
from common.response import success_response
from promotion.models import SuperDiscount
from promotion.permissions import HasPromotionCreate, HasPromotionRead, HasPromotionUpdate
from promotion.serializers import SuperDiscountSerializer


def get_active_super_discount() -> SuperDiscount | None:
    now = timezone.now()
    return (
        SuperDiscount.objects.filter(is_active=True)
        .filter(Q(start_time__isnull=True) | Q(start_time__lte=now))
        .filter(Q(end_time__isnull=True) | Q(end_time__gte=now))
        .order_by('-id')
        .first()
    )


class SuperDiscountActiveView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        campaign = get_active_super_discount()
        if campaign is None:
            return success_response(data=None)
        return success_response(data=SuperDiscountSerializer(campaign).data)


class SuperDiscountViewSet(viewsets.ModelViewSet):
    queryset = SuperDiscount.objects.all().order_by('-id')
    serializer_class = SuperDiscountSerializer
    pagination_class = StandardPagination

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated(), HasPromotionRead()]
        if self.action == 'create':
            return [IsAuthenticated(), HasPromotionCreate()]
        return [IsAuthenticated(), HasPromotionUpdate()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
