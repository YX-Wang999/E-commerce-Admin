"""Platform admin monitoring for seller points."""

from datetime import timedelta

from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination
from common.response import success_response
from points.permissions import HasPointsRead
from seller_points.models import SellerPointsRule, SellerPointsTransaction
from seller_points.serializers import SellerPointsTransactionSerializer
from tenants.models import Tenant


class AdminSellerPointsOverviewView(APIView):
    permission_classes = [IsAuthenticated, HasPointsRead]

    def get(self, request: Request) -> Response:
        since = timezone.now() - timedelta(hours=24)
        recent_earn = (
            SellerPointsTransaction.objects.filter(created_at__gte=since, amount__gt=0)
            .values('tenant_id')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')[:20]
        )
        tenant_ids = [row['tenant_id'] for row in recent_earn]
        tenant_map = {t.id: t.name for t in Tenant.objects.filter(id__in=tenant_ids)}
        alerts = []
        for row in recent_earn:
            total = row['total'] or 0
            if total >= 5000:
                alerts.append({
                    'tenant_id': row['tenant_id'],
                    'tenant_name': tenant_map.get(row['tenant_id'], ''),
                    'total_issued': total,
                    'transaction_count': row['count'],
                    'message': '24小时内发放积分异常偏高',
                })
        enriched = [
            {
                **row,
                'tenant_name': tenant_map.get(row['tenant_id'], ''),
            }
            for row in recent_earn
        ]
        return success_response(
            data={
                'active_tenant_rules': SellerPointsRule.objects.filter(is_active=True).count(),
                'recent_high_issue': enriched,
                'alerts': alerts,
            },
        )


class AdminSellerPointsTransactionListView(APIView):
    permission_classes = [IsAuthenticated, HasPointsRead]

    def get(self, request: Request) -> Response:
        queryset = SellerPointsTransaction.objects.select_related('customer', 'tenant').all()
        tenant_id = request.query_params.get('tenant_id')
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset.order_by('-id'), request)
        data = SellerPointsTransactionSerializer(page, many=True).data
        for item, obj in zip(data, page):
            item['tenant_name'] = obj.tenant.name if obj.tenant_id else ''
        return paginator.get_paginated_response(data)
