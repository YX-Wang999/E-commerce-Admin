"""Review API views."""

from __future__ import annotations

import logging

from django.db.models import Exists, OuterRef
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination
from common.response import error_response, success_response
from customers.permissions import IsCustomerAuthenticated
from customers.utils import get_request_customer
from reviews.models import ProductReview, ReviewComment, ReviewLike
from reviews.serializers import (
    ReviewCommentSerializer,
    ReviewCreateSerializer,
    ReviewFollowUpSerializer,
    serialize_comment,
    serialize_review,
)
from reviews.services import (
    add_comment,
    can_follow_up,
    follow_up_candidates,
    increment_view_count,
    pending_review_items,
    product_review_stats,
    published_reviews,
    toggle_like,
    validate_review_create,
)

logger = logging.getLogger(__name__)


def _viewer_id(request: Request) -> int | None:
    customer = get_request_customer(request)
    return customer.id if customer else None


def _liked_map(review_ids: list[int], customer_id: int | None) -> dict[int, bool]:
    if not customer_id or not review_ids:
        return {}
    liked_ids = set(
        ReviewLike.objects.filter(review_id__in=review_ids, customer_id=customer_id).values_list(
            'review_id', flat=True,
        ),
    )
    return {rid: rid in liked_ids for rid in review_ids}


class ReviewCreateView(APIView):
    permission_classes = [IsAuthenticated, IsCustomerAuthenticated]

    def post(self, request: Request) -> Response:
        customer = get_request_customer(request)
        serializer = ReviewCreateSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        data = serializer.validated_data
        try:
            product, order = validate_review_create(
                customer=customer,
                product_id=data['product_id'],
                order_id=data.get('order_id'),
            )
        except ValueError as exc:
            return error_response(str(exc))
        try:
            review = ProductReview.objects.create(
                customer=customer,
                product=product,
                order=order,
                tenant_id=product.tenant_id,
                rating=data['rating'],
                content=data['content'],
                images=data.get('images') or [],
                video=data.get('video') or '',
                is_anonymous=data.get('is_anonymous', False),
                allow_comment=data.get('allow_comment', True),
            )
        except Exception:
            logger.exception('Create review failed')
            return error_response('提交评价失败', code=50000, http_status=500)
        try:
            from notification.services import notify_review_created

            notify_review_created(review=review)
        except Exception:
            logger.exception('Notify review created failed')
        return success_response(
            data=serialize_review(review, viewer_id=customer.id),
            message='评价提交成功',
        )


class ReviewUserCenterView(APIView):
    permission_classes = [IsAuthenticated, IsCustomerAuthenticated]

    def get(self, request: Request) -> Response:
        customer = get_request_customer(request)
        tab = (request.query_params.get('tab') or 'pending').strip()
        if tab == 'pending':
            return success_response(data={'items': pending_review_items(customer), 'tab': tab})
        if tab == 'follow_up':
            reviews = follow_up_candidates(customer)
            ids = [r.id for r in reviews]
            liked = _liked_map(ids, customer.id)
            return success_response(data={
                'items': [serialize_review(r, viewer_id=customer.id, liked=liked.get(r.id, False)) for r in reviews],
                'tab': tab,
            })
        reviews = published_reviews().filter(customer=customer).select_related('product', 'order')
        ids = list(reviews.values_list('id', flat=True)[:50])
        liked = _liked_map(ids, customer.id)
        items = [
            serialize_review(r, viewer_id=customer.id, liked=liked.get(r.id, False))
            for r in reviews[:50]
        ]
        return success_response(data={'items': items, 'tab': 'reviewed'})


class ProductReviewListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request, product_id: int) -> Response:
        viewer = _viewer_id(request)
        qs = published_reviews().filter(product_id=product_id).select_related('customer', 'product', 'order')
        stats = product_review_stats(product_id)
        page = int(request.query_params.get('page') or 1)
        page_size = min(int(request.query_params.get('page_size') or 10), 50)
        start = (page - 1) * page_size
        end = start + page_size
        batch = list(qs[start:end])
        liked = _liked_map([r.id for r in batch], viewer)
        return success_response(data={
            **stats,
            'results': [
                serialize_review(r, viewer_id=viewer, liked=liked.get(r.id, False))
                for r in batch
            ],
            'count': qs.count(),
            'page': page,
            'page_size': page_size,
        })


class ReviewDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request, pk: int) -> Response:
        viewer = _viewer_id(request)
        review = published_reviews().filter(pk=pk).select_related('customer', 'product', 'order').first()
        if review is None:
            customer = get_request_customer(request)
            if customer:
                review = ProductReview.objects.filter(pk=pk, customer=customer).select_related(
                    'customer', 'product', 'order',
                ).first()
        if review is None:
            return error_response('评价不存在', http_status=404)
        liked = ReviewLike.objects.filter(review=review, customer_id=viewer).exists() if viewer else False
        return success_response(data=serialize_review(review, viewer_id=viewer, liked=liked))

    def delete(self, request: Request, pk: int) -> Response:
        customer = get_request_customer(request)
        if customer is None:
            return error_response('请先登录', http_status=401)
        review = ProductReview.objects.filter(pk=pk, customer=customer).first()
        if review is None:
            return error_response('评价不存在', http_status=404)
        review.status = ProductReview.STATUS_DELETED
        review.is_public = False
        review.save(update_fields=['status', 'is_public', 'updated_at'])
        return success_response(message='评价已删除')


class ReviewLikeView(APIView):
    permission_classes = [IsAuthenticated, IsCustomerAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        customer = get_request_customer(request)
        try:
            liked, like_count = toggle_like(pk, customer.id)
        except ValueError as exc:
            return error_response(str(exc))
        try:
            if liked:
                from notification.services import notify_review_liked

                notify_review_liked(review_id=pk, actor_id=customer.id)
        except Exception:
            logger.exception('Notify review liked failed')
        return success_response(data={'liked': liked, 'like_count': like_count})


class ReviewCommentCreateView(APIView):
    permission_classes = [IsAuthenticated, IsCustomerAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        customer = get_request_customer(request)
        serializer = ReviewCommentSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            comment = add_comment(pk, customer.id, serializer.validated_data['content'])
        except ValueError as exc:
            return error_response(str(exc))
        try:
            from notification.services import notify_review_commented

            notify_review_commented(review_id=pk, actor_id=customer.id, comment_id=comment.id)
        except Exception:
            logger.exception('Notify review commented failed')
        return success_response(
            data=serialize_comment(comment, viewer_id=customer.id),
            message='评论成功',
        )


class ReviewCommentListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request, pk: int) -> Response:
        viewer = _viewer_id(request)
        if not published_reviews().filter(pk=pk).exists():
            return error_response('评价不存在', http_status=404)
        comments = ReviewComment.objects.filter(review_id=pk).select_related('customer')[:100]
        return success_response(data={
            'results': [serialize_comment(c, viewer_id=viewer) for c in comments],
        })


class ReviewViewIncrementView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request, pk: int) -> Response:
        if published_reviews().filter(pk=pk).exists():
            increment_view_count(pk)
        review = published_reviews().filter(pk=pk).first()
        count = review.view_count if review else 0
        return success_response(data={'view_count': count})


class ReviewFollowUpView(APIView):
    permission_classes = [IsAuthenticated, IsCustomerAuthenticated]

    def post(self, request: Request, pk: int) -> Response:
        customer = get_request_customer(request)
        review = ProductReview.objects.filter(pk=pk, customer=customer).exclude(
            status=ProductReview.STATUS_DELETED,
        ).first()
        if review is None:
            return error_response('评价不存在', http_status=404)
        if not can_follow_up(review):
            return error_response('不可追评或已超过追评期限')
        serializer = ReviewFollowUpSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        data = serializer.validated_data
        review.follow_up_content = data['content']
        review.follow_up_images = data.get('images') or []
        review.follow_up_video = data.get('video') or ''
        review.follow_up_at = timezone.now()
        review.save(update_fields=[
            'follow_up_content', 'follow_up_images', 'follow_up_video', 'follow_up_at', 'updated_at',
        ])
        return success_response(
            data=serialize_review(review, viewer_id=customer.id),
            message='追评成功',
        )


class ProductReviewSubmitView(APIView):
    """Legacy mall review submission (customer_id in body)."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        from points.serializers import ProductReviewSubmitSerializer

        serializer = ProductReviewSubmitSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        data = serializer.validated_data
        from customers.models import Customer

        customer = Customer.objects.filter(pk=data['customer_id'], is_active=True).first()
        if customer is None:
            return error_response('会员不存在')
        try:
            product, order = validate_review_create(
                customer=customer,
                product_id=data['product_id'],
                order_id=data.get('order_id'),
            )
        except ValueError as exc:
            return error_response(str(exc))
        review = ProductReview.objects.create(
            customer=customer,
            product=product,
            order=order,
            tenant_id=product.tenant_id,
            rating=data['rating'],
            content=data['content'],
        )
        return success_response(data={'id': review.id}, message='评价提交成功')
