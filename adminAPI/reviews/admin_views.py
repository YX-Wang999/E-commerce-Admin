"""Platform admin review management."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination
from common.response import error_response, success_response
from orders.role_filters import resolve_role_codes
from reviews.models import ProductReview
from reviews.serializers import serialize_review


def _can_manage_reviews(user) -> bool:
    if getattr(user, 'is_superuser', False):
        return True
    roles = resolve_role_codes(user)
    return bool(roles & {'super_admin', 'ops_manager', 'ops_staff', 'cs_manager', 'cs_staff'})


class AdminReviewListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        if not _can_manage_reviews(request.user):
            return error_response('无权查看', http_status=403)
        qs = ProductReview.objects.exclude(status=ProductReview.STATUS_DELETED).select_related(
            'customer', 'product', 'order', 'tenant',
        )
        keyword = (request.query_params.get('keyword') or '').strip()
        if keyword:
            qs = qs.filter(product__name__icontains=keyword)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        items = [serialize_review(r, viewer_id=None) for r in page]
        return paginator.get_paginated_response(items)


class AdminReviewDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request: Request, pk: int) -> Response:
        if not _can_manage_reviews(request.user):
            return error_response('无权操作', http_status=403)
        review = ProductReview.objects.filter(pk=pk).first()
        if review is None:
            return error_response('评价不存在', http_status=404)
        review.status = ProductReview.STATUS_DELETED
        review.is_public = False
        review.save(update_fields=['status', 'is_public', 'updated_at'])
        return success_response(message='评价已删除')
