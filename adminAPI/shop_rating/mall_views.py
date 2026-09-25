"""Mall shop rating APIs."""

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.response import error_response, success_response
from shop_rating.models import UserRating
from shop_rating.serializers import ShopRatingSerializer, UserRatingSerializer
from shop_rating.services import ensure_shop_rating, get_tenant_rating_display
from tenants.models import Tenant


class MallTenantRatingView(APIView):
    """Public tenant rating summary."""

    permission_classes = [AllowAny]

    def get(self, request: Request, tenant_id: int) -> Response:
        try:
            tenant = Tenant.objects.get(pk=tenant_id, status=Tenant.STATUS_ACTIVE)
        except Tenant.DoesNotExist:
            return error_response('店铺不存在')
        rating = ensure_shop_rating(tenant)
        payload = ShopRatingSerializer(rating).data
        payload['tenant_name'] = tenant.name
        payload['display'] = get_tenant_rating_display(tenant.id)
        return success_response(payload)


class MallTenantReviewsView(APIView):
    """Public tenant reviews."""

    permission_classes = [AllowAny]

    def get(self, request: Request, tenant_id: int) -> Response:
        if not Tenant.objects.filter(pk=tenant_id, status=Tenant.STATUS_ACTIVE).exists():
            return error_response('店铺不存在')
        rows = UserRating.objects.filter(tenant_id=tenant_id).order_by('-id')[:50]
        return success_response(UserRatingSerializer(rows, many=True).data)
