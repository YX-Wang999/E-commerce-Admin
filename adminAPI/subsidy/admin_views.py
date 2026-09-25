"""Platform admin subsidy API views."""

from __future__ import annotations

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination
from common.response import error_response, success_response
from subsidy.models import SubsidyOrder, SubsidyPolicy, SubsidyProduct
from subsidy.permissions import HasSubsidyCreate, HasSubsidyRead, HasSubsidyUpdate
from subsidy.serializers import (
    GovernmentFilingSyncSerializer,
    SubsidyOrderSerializer,
    SubsidyPolicySerializer,
    SubsidyProductSerializer,
)
from subsidy.services import apply_filing_approved, subsidy_stats


class SubsidyPolicyViewSet(viewsets.ModelViewSet):
    queryset = SubsidyPolicy.objects.all().order_by('-created_at')
    serializer_class = SubsidyPolicySerializer
    pagination_class = StandardPagination

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated(), HasSubsidyRead()]
        if self.action == 'create':
            return [IsAuthenticated(), HasSubsidyCreate()]
        return [IsAuthenticated(), HasSubsidyUpdate()]


class SubsidyProductAdminViewSet(viewsets.ReadOnlyModelViewSet):
    """Monitor government filing status — platform does not audit merchants."""

    queryset = (
        SubsidyProduct.objects.select_related('product', 'tenant', 'policy')
        .all()
        .order_by('-created_at')
    )
    serializer_class = SubsidyProductSerializer
    pagination_class = StandardPagination

    def get_permissions(self):
        if self.action == 'sync_filing':
            return [IsAuthenticated(), HasSubsidyUpdate()]
        return [IsAuthenticated(), HasSubsidyRead()]

    def get_queryset(self):
        qs = super().get_queryset()
        filing_status = self.request.query_params.get('filing_status')
        if filing_status:
            qs = qs.filter(filing_status=filing_status)
        keyword = (self.request.query_params.get('keyword') or '').strip()
        if keyword:
            qs = qs.filter(product__name__icontains=keyword)
        region = (self.request.query_params.get('region') or '').strip()
        if region:
            qs = qs.filter(region=region)
        return qs

    @action(detail=True, methods=['post'], url_path='sync-filing')
    def sync_filing(self, request: Request, pk=None) -> Response:
        """Record government filing callback status (not platform audit)."""
        row = self.get_object()
        serializer = GovernmentFilingSyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        filing_status = serializer.validated_data['filing_status']

        row.filing_status = filing_status
        if filing_status == SubsidyProduct.FILING_REJECTED:
            row.filing_reject_reason = serializer.validated_data.get('filing_reject_reason', '').strip()
            row.subsidy_amount = 0
        elif filing_status == SubsidyProduct.FILING_APPROVED:
            row.filing_reject_reason = ''
            apply_filing_approved(row)
            return success_response(SubsidyProductSerializer(row).data, message='已同步政府备案通过状态')
        else:
            row.filing_reject_reason = ''
            if not row.filing_submitted_at:
                row.filing_submitted_at = timezone.now()

        row.save(
            update_fields=[
                'filing_status',
                'filing_reject_reason',
                'filing_submitted_at',
                'subsidy_amount',
                'updated_at',
            ],
        )
        return success_response(SubsidyProductSerializer(row).data, message='备案状态已同步')


class SubsidyOrderAdminViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        SubsidyOrder.objects.select_related('order', 'order__customer', 'tenant')
        .prefetch_related('order__items')
        .all()
        .order_by('-created_at')
    )
    serializer_class = SubsidyOrderSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated, HasSubsidyRead]

    def get_queryset(self):
        qs = super().get_queryset()
        gov_status = self.request.query_params.get('government_status')
        if gov_status:
            qs = qs.filter(government_status=gov_status)
        return qs

    @action(detail=True, methods=['post'], url_path='report')
    def report(self, request: Request, pk=None) -> Response:
        row = self.get_object()
        row.government_status = SubsidyOrder.GOV_REPORTED
        row.reported_at = timezone.now()
        row.save(update_fields=['government_status', 'reported_at', 'updated_at'])
        return success_response(SubsidyOrderSerializer(row).data, message='已标记为已上报')


class SubsidyStatsView(APIView):
    permission_classes = [IsAuthenticated, HasSubsidyRead]

    def get(self, request: Request) -> Response:
        return success_response(subsidy_stats())
