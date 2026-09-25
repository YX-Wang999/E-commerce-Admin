"""Seller shop rating APIs."""

from decimal import Decimal

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.response import error_response, success_response
from shop_rating.models import RatingAdjustmentRequest
from shop_rating.serializers import (
    RatingAdjustmentApplySerializer,
    RatingAdjustmentRequestSerializer,
    ShopRatingSerializer,
    UserRatingSerializer,
)
from shop_rating.services import ensure_shop_rating, get_tenant_rating_display
from tenants.seller_permissions import IsTenantStaffManager, IsTenantStaffMember


class SellerShopRatingView(APIView):
    """Current tenant shop rating."""

    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        tenant = request.tenant
        if not tenant:
            return error_response('未找到商家信息')
        rating = ensure_shop_rating(tenant)
        payload = ShopRatingSerializer(rating).data
        payload['display'] = get_tenant_rating_display(tenant.id)
        return success_response(payload)


class SellerShopRatingReviewsView(APIView):
    """Recent user ratings for tenant."""

    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        tenant = request.tenant
        if not tenant:
            return error_response('未找到商家信息')
        from shop_rating.models import UserRating

        rows = UserRating.objects.filter(tenant=tenant).order_by('-id')[:50]
        return success_response(UserRatingSerializer(rows, many=True).data)


class SellerRatingAdjustmentRequestView(APIView):
    """Apply for score adjustment (±0.5)."""

    permission_classes = [IsAuthenticated, IsTenantStaffManager]

    def get(self, request: Request) -> Response:
        tenant = request.tenant
        if not tenant:
            return error_response('未找到商家信息')
        rows = RatingAdjustmentRequest.objects.filter(tenant=tenant).order_by('-id')[:20]
        return success_response(RatingAdjustmentRequestSerializer(rows, many=True).data)

    def post(self, request: Request) -> Response:
        tenant = request.tenant
        if not tenant:
            return error_response('未找到商家信息')

        serializer = RatingAdjustmentApplySerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))

        rating = ensure_shop_rating(tenant)
        current_score = Decimal(str(rating.overall_score))
        requested_score = serializer.validated_data['requested_score']
        delta = abs(requested_score - current_score)
        if delta > Decimal('0.5'):
            return error_response('单次调整幅度不能超过 0.5 分')
        if delta == 0:
            return error_response('申请分数与当前分数相同')

        pending = RatingAdjustmentRequest.objects.filter(
            tenant=tenant,
            status=RatingAdjustmentRequest.STATUS_PENDING,
        ).exists()
        if pending:
            return error_response('已有待审核的评分调整申请')

        row = RatingAdjustmentRequest.objects.create(
            tenant=tenant,
            current_score=current_score,
            requested_score=requested_score,
            reason=serializer.validated_data['reason'].strip(),
        )
        return success_response(
            RatingAdjustmentRequestSerializer(row).data,
            message='申请已提交，等待平台审核',
        )
