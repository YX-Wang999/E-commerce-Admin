"""Review serializers."""

from rest_framework import serializers

from common.media_utils import file_field_url
from reviews.models import ProductReview, ReviewComment


class ReviewCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    order_id = serializers.IntegerField(required=False, allow_null=True)
    rating = serializers.IntegerField(min_value=1, max_value=5, default=5)
    content = serializers.CharField(max_length=500)
    images = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False,
        default=list,
    )
    video = serializers.URLField(required=False, allow_blank=True, default='')
    is_anonymous = serializers.BooleanField(default=False)
    allow_comment = serializers.BooleanField(default=True)


class ReviewFollowUpSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=500)
    images = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False,
        default=list,
    )
    video = serializers.URLField(required=False, allow_blank=True, default='')


class ReviewCommentSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=500)


def _customer_display(review: ProductReview, viewer_id: int | None = None) -> dict:
    if review.is_anonymous and review.customer_id != viewer_id:
        return {'id': None, 'nickname': '匿名用户', 'avatar': ''}
    customer = review.customer
    return {
        'id': customer.id,
        'nickname': customer.display_name or customer.nickname or customer.phone or '用户',
        'avatar': '',
    }


def serialize_review(
    review: ProductReview,
    *,
    viewer_id: int | None = None,
    liked: bool = False,
    include_product: bool = True,
) -> dict:
    data = {
        'id': review.id,
        'rating': review.rating,
        'content': review.content,
        'images': review.images or [],
        'video': review.video or '',
        'is_anonymous': review.is_anonymous,
        'allow_comment': review.allow_comment,
        'is_public': review.is_public,
        'view_count': review.view_count,
        'like_count': review.like_count,
        'comment_count': review.comment_count,
        'status': review.status,
        'created_at': review.created_at.isoformat() if review.created_at else None,
        'follow_up_content': review.follow_up_content or '',
        'follow_up_images': review.follow_up_images or [],
        'follow_up_video': review.follow_up_video or '',
        'follow_up_at': review.follow_up_at.isoformat() if review.follow_up_at else None,
        'can_follow_up': review.customer_id == viewer_id and not review.follow_up_content,
        'customer': _customer_display(review, viewer_id),
        'liked': liked,
        'order_id': review.order_id,
    }
    if include_product and review.product_id:
        product = review.product
        image = file_field_url(product.image, getattr(product, 'updated_at', None))
        data['product'] = {
            'id': product.id,
            'name': product.name,
            'image': image,
        }
    if review.order_id and review.order:
        data['order_no'] = review.order.order_no
    return data


def serialize_comment(comment: ReviewComment, viewer_id: int | None = None) -> dict:
    customer = comment.customer
    return {
        'id': comment.id,
        'content': comment.content,
        'created_at': comment.created_at.isoformat() if comment.created_at else None,
        'customer': {
            'id': customer.id,
            'nickname': customer.display_name or customer.nickname or customer.phone or '用户',
            'is_self': customer.id == viewer_id,
        },
    }
