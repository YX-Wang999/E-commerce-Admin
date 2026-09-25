"""Review business logic."""

from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.db.models import Avg, Count, F, Q
from django.utils import timezone

from common.media_utils import file_field_url
from orders.models import Order, OrderItem
from products.models import Product
from reviews.models import ProductReview, ReviewComment, ReviewLike

FOLLOW_UP_DAYS = 30


def published_reviews():
    return ProductReview.objects.filter(status=ProductReview.STATUS_PUBLISHED, is_public=True)


def increment_view_count(review_id: int) -> None:
    ProductReview.objects.filter(pk=review_id, status=ProductReview.STATUS_PUBLISHED).update(
        view_count=F('view_count') + 1,
    )


@transaction.atomic
def toggle_like(review_id: int, customer_id: int) -> tuple[bool, int]:
    review = ProductReview.objects.select_for_update().filter(
        pk=review_id,
        status=ProductReview.STATUS_PUBLISHED,
    ).first()
    if review is None:
        raise ValueError('评价不存在')
    like = ReviewLike.objects.filter(review_id=review_id, customer_id=customer_id).first()
    if like:
        like.delete()
        ProductReview.objects.filter(pk=review_id).update(like_count=F('like_count') - 1)
        review.refresh_from_db(fields=['like_count'])
        return False, review.like_count
    ReviewLike.objects.create(review_id=review_id, customer_id=customer_id)
    ProductReview.objects.filter(pk=review_id).update(like_count=F('like_count') + 1)
    review.refresh_from_db(fields=['like_count'])
    return True, review.like_count


@transaction.atomic
def add_comment(review_id: int, customer_id: int, content: str) -> ReviewComment:
    review = ProductReview.objects.select_for_update().filter(
        pk=review_id,
        status=ProductReview.STATUS_PUBLISHED,
    ).first()
    if review is None:
        raise ValueError('评价不存在')
    if not review.allow_comment:
        raise ValueError('该评价不允许评论')
    comment = ReviewComment.objects.create(
        review_id=review_id,
        customer_id=customer_id,
        content=content,
    )
    ProductReview.objects.filter(pk=review_id).update(comment_count=F('comment_count') + 1)
    return comment


def product_review_stats(product_id: int) -> dict:
    qs = published_reviews().filter(product_id=product_id)
    agg = qs.aggregate(avg_rating=Avg('rating'), total=Count('id'))
    avg = agg['avg_rating'] or 0
    return {
        'average_rating': round(float(avg), 1),
        'review_count': agg['total'] or 0,
    }


def pending_review_items(customer) -> list[dict]:
    """Completed order items without a review."""
    completed_orders = Order.objects.filter(
        customer=customer,
        status=Order.STATUS_COMPLETED,
    ).prefetch_related('items__product')
    reviewed_pairs = set(
        ProductReview.objects.filter(
            customer=customer,
            order_id__isnull=False,
        ).exclude(status=ProductReview.STATUS_DELETED).values_list('order_id', 'product_id'),
    )
    items = []
    for order in completed_orders:
        for item in order.items.all():
            key = (order.id, item.product_id)
            if key in reviewed_pairs:
                continue
            image = file_field_url(item.product.image, getattr(item.product, 'updated_at', None)) if item.product and item.product.image else ''
            items.append({
                'order_id': order.id,
                'order_no': order.order_no,
                'product_id': item.product_id,
                'product_name': item.product_name,
                'product_image': image,
                'unit_price': str(item.unit_price),
                'quantity': item.quantity,
                'completed_at': order.completed_at or order.updated_at,
            })
    return items


def follow_up_candidates(customer) -> list[ProductReview]:
    cutoff = timezone.now() - timedelta(days=FOLLOW_UP_DAYS)
    return list(
        published_reviews().filter(
            customer=customer,
            follow_up_content='',
            created_at__gte=cutoff,
        ).select_related('product', 'order'),
    )


def can_follow_up(review: ProductReview) -> bool:
    if review.follow_up_content:
        return False
    cutoff = timezone.now() - timedelta(days=FOLLOW_UP_DAYS)
    return review.created_at >= cutoff


def validate_review_create(*, customer, product_id: int, order_id: int | None) -> tuple[Product, Order | None]:
    product = Product.objects.filter(pk=product_id, is_active=True).first()
    if product is None:
        raise ValueError('商品不存在')
    order = None
    if order_id:
        order = Order.objects.filter(pk=order_id, customer=customer).first()
        if order is None:
            raise ValueError('订单不存在')
        if order.status != Order.STATUS_COMPLETED:
            raise ValueError('仅已完成订单可评价')
        if not OrderItem.objects.filter(order=order, product_id=product_id).exists():
            raise ValueError('订单中无此商品')
        exists = ProductReview.objects.filter(
            customer=customer,
            product_id=product_id,
            order_id=order_id,
        ).exclude(status=ProductReview.STATUS_DELETED).exists()
        if exists:
            raise ValueError('该订单商品已评价')
    return product, order
