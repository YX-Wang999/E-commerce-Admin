"""Platform admin shop rating APIs."""

from decimal import Decimal

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.response import error_response, success_response
from shop_rating.models import RatingAdjustmentLog, RatingAdjustmentRequest, RatingScoreHistory, ShopRating
from shop_rating.serializers import (
    RatingAdjustmentRequestSerializer,
    RatingAdjustmentReviewSerializer,
    ShopRatingSerializer,
)
from shop_rating.services import detect_rating_alerts, update_shop_score


class AdminShopRatingListView(APIView):
    """List shop ratings; filter low-score tenants."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        threshold = request.query_params.get('max_score', '4.0')
        try:
            max_score = Decimal(str(threshold))
        except Exception:
            max_score = Decimal('4.0')

        only_low = request.query_params.get('low_only', 'false').lower() in {'1', 'true', 'yes'}
        qs = ShopRating.objects.select_related('tenant').order_by('overall_score', '-total_ratings')
        if only_low:
            qs = qs.filter(overall_score__lt=max_score)

        rows = []
        for row in qs[:100]:
            rows.append(
                {
                    'tenant_id': row.tenant_id,
                    'tenant_name': row.tenant.name,
                    'tenant_code': row.tenant.code,
                    **ShopRatingSerializer(row).data,
                },
            )
        return success_response(rows)


class AdminShopRatingTrendView(APIView):
    """Recent score trend for a tenant."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        tenant_id = request.query_params.get('tenant_id')
        if not tenant_id:
            return error_response('请指定商家')
        since = timezone.now() - timezone.timedelta(days=30)
        history = RatingScoreHistory.objects.filter(
            tenant_id=tenant_id,
            recorded_at__gte=since,
        ).order_by('recorded_at')[:200]
        data = [
            {
                'score': float(item.overall_score),
                'recorded_at': item.recorded_at.isoformat(),
            }
            for item in history
        ]
        return success_response(data)


class AdminShopRatingAlertView(APIView):
    """Rating anomaly alerts."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        days = int(request.query_params.get('days') or 1)
        return success_response(detect_rating_alerts(days=max(1, days)))


class AdminRatingAdjustmentListView(APIView):
    """List and review merchant rating adjustment requests."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        status_value = request.query_params.get('status')
        qs = RatingAdjustmentRequest.objects.select_related('tenant').order_by('-id')
        if status_value:
            qs = qs.filter(status=status_value)
        rows = []
        for item in qs[:100]:
            payload = RatingAdjustmentRequestSerializer(item).data
            payload['tenant_name'] = item.tenant.name
            rows.append(payload)
        return success_response(rows)


class AdminRatingAdjustmentReviewView(APIView):
    """Review a rating adjustment request."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        serializer = RatingAdjustmentReviewSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))

        try:
            row = RatingAdjustmentRequest.objects.select_related('tenant').get(pk=pk)
        except RatingAdjustmentRequest.DoesNotExist:
            return error_response('申请不存在')
        if row.status != RatingAdjustmentRequest.STATUS_PENDING:
            return error_response('该申请已处理')

        status_value = serializer.validated_data['status']
        review_note = serializer.validated_data.get('review_note') or ''
        row.status = (
            RatingAdjustmentRequest.STATUS_APPROVED
            if status_value == 'approved'
            else RatingAdjustmentRequest.STATUS_REJECTED
        )
        row.reviewer = request.user
        row.review_note = review_note
        row.reviewed_at = timezone.now()
        row.save(update_fields=['status', 'reviewer', 'review_note', 'reviewed_at'])

        if row.status == RatingAdjustmentRequest.STATUS_APPROVED:
            rating = update_shop_score(row.tenant)
            old_score = rating.overall_score
            rating.overall_score = row.requested_score
            rating.save(update_fields=['overall_score', 'updated_at'])
            RatingAdjustmentLog.objects.create(
                tenant=row.tenant,
                operator=request.user,
                old_score=old_score,
                new_score=row.requested_score,
                reason=f'平台审核通过：{row.reason}',
            )

        return success_response(RatingAdjustmentRequestSerializer(row).data, message='审核完成')
