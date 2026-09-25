"""Shop rating calculation and helpers."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from django.db.models import Avg, Count, Q
from django.utils import timezone

from orders.models import Order, Refund
from shop_rating.models import RatingScoreHistory, ShopRating, UserRating

DEFAULT_INITIAL_SCORE = Decimal('5.0')
QUALITY_WEIGHT = Decimal('0.40')
SERVICE_WEIGHT = Decimal('0.25')
LOGISTICS_WEIGHT = Decimal('0.20')
REVIEW_WEIGHT = Decimal('0.85')
COMPLETION_WEIGHT = Decimal('0.10')
REFUND_WEIGHT = Decimal('0.05')


def _round_score(value: Decimal | float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)


def get_rating_label(score: float | Decimal) -> str:
    value = float(score)
    if value >= 4.8:
        return 'excellent'
    if value >= 4.5:
        return 'good'
    if value >= 4.0:
        return 'fair'
    return 'needs_improvement'


def get_initial_weights(rating_count: int) -> tuple[float, float]:
    if rating_count <= 0:
        return 1.0, 0.0
    if rating_count <= 10:
        return 0.7, 0.3
    if rating_count <= 30:
        return 0.4, 0.6
    if rating_count <= 50:
        return 0.2, 0.8
    return 0.0, 1.0


def apply_initial_decay(
    real_score: Decimal,
    rating_count: int,
    initial_score: Decimal = DEFAULT_INITIAL_SCORE,
) -> Decimal:
    initial_weight, real_weight = get_initial_weights(rating_count)
    if rating_count <= 0:
        return initial_score
    blended = initial_score * Decimal(str(initial_weight)) + real_score * Decimal(str(real_weight))
    return _round_score(blended)


def _review_dimension_averages(tenant_id: int) -> dict[str, Decimal | None]:
    aggregates = UserRating.objects.filter(tenant_id=tenant_id).aggregate(
        quality=Avg('quality_score'),
        service=Avg('service_score'),
        logistics=Avg('logistics_score'),
        count=Count('id'),
    )
    count = int(aggregates.get('count') or 0)
    if count <= 0:
        return {
            'quality': None,
            'service': None,
            'logistics': None,
            'composite': None,
            'count': 0,
        }

    quality = Decimal(str(aggregates['quality']))
    service = Decimal(str(aggregates['service']))
    logistics = Decimal(str(aggregates['logistics']))
    composite = (
        quality * QUALITY_WEIGHT
        + service * SERVICE_WEIGHT
        + logistics * LOGISTICS_WEIGHT
    )
    return {
        'quality': _round_score(quality),
        'service': _round_score(service),
        'logistics': _round_score(logistics),
        'composite': _round_score(composite),
        'count': count,
    }


def _order_stats(tenant_id: int) -> dict[str, int]:
    base_qs = Order.objects.filter(tenant_id=tenant_id).exclude(status=Order.STATUS_PENDING)
    total_orders = base_qs.count()
    completed_orders = base_qs.filter(status=Order.STATUS_COMPLETED).count()
    refund_orders = Refund.objects.filter(
        order__tenant_id=tenant_id,
        status__in=[Refund.STATUS_APPROVED, Refund.STATUS_PENDING],
    ).count()
    return {
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'refund_orders': refund_orders,
    }


def compute_composite_real_score(tenant_id: int) -> Decimal:
    review_stats = _review_dimension_averages(tenant_id)
    order_stats = _order_stats(tenant_id)

    if review_stats['composite'] is None:
        review_component = DEFAULT_INITIAL_SCORE
    else:
        review_component = review_stats['composite']

    total_orders = order_stats['total_orders']
    if total_orders <= 0:
        completion_score = DEFAULT_INITIAL_SCORE
        refund_score = DEFAULT_INITIAL_SCORE
    else:
        completion_rate = order_stats['completed_orders'] / total_orders
        refund_rate = order_stats['refund_orders'] / total_orders
        completion_score = _round_score(Decimal(str(completion_rate)) * DEFAULT_INITIAL_SCORE)
        refund_score = _round_score((Decimal('1') - Decimal(str(refund_rate))) * DEFAULT_INITIAL_SCORE)

    composite = (
        review_component * REVIEW_WEIGHT
        + completion_score * COMPLETION_WEIGHT
        + refund_score * REFUND_WEIGHT
    )
    return _round_score(composite)


def ensure_shop_rating(tenant) -> ShopRating:
    rating, _ = ShopRating.objects.get_or_create(
        tenant=tenant,
        defaults={'initial_score': DEFAULT_INITIAL_SCORE},
    )
    return rating


def update_shop_score(tenant) -> ShopRating:
    """Recalculate and persist tenant shop score."""
    rating = ensure_shop_rating(tenant)
    review_stats = _review_dimension_averages(tenant.id)
    order_stats = _order_stats(tenant.id)
    real_score = compute_composite_real_score(tenant.id)
    final_score = apply_initial_decay(real_score, review_stats['count'], rating.initial_score)

    rating.overall_score = final_score
    if review_stats['count'] > 0:
        rating.quality_score = apply_initial_decay(
            review_stats['quality'] or DEFAULT_INITIAL_SCORE,
            review_stats['count'],
            rating.initial_score,
        )
        rating.service_score = apply_initial_decay(
            review_stats['service'] or DEFAULT_INITIAL_SCORE,
            review_stats['count'],
            rating.initial_score,
        )
        rating.logistics_score = apply_initial_decay(
            review_stats['logistics'] or DEFAULT_INITIAL_SCORE,
            review_stats['count'],
            rating.initial_score,
        )
    else:
        rating.quality_score = rating.initial_score
        rating.service_score = rating.initial_score
        rating.logistics_score = rating.initial_score

    rating.total_ratings = review_stats['count']
    rating.total_orders = order_stats['total_orders']
    rating.completed_orders = order_stats['completed_orders']
    rating.refund_orders = order_stats['refund_orders']
    rating.save()

    RatingScoreHistory.objects.create(
        tenant=tenant,
        overall_score=rating.overall_score,
    )
    return rating


def get_tenant_rating_display(tenant_id: int) -> dict[str, Any]:
    """Return rating payload for serializers."""
    try:
        rating = ShopRating.objects.get(tenant_id=tenant_id)
    except ShopRating.DoesNotExist:
        return {
            'overall_score': float(DEFAULT_INITIAL_SCORE),
            'quality_score': float(DEFAULT_INITIAL_SCORE),
            'service_score': float(DEFAULT_INITIAL_SCORE),
            'logistics_score': float(DEFAULT_INITIAL_SCORE),
            'total_ratings': 0,
            'rating_label': get_rating_label(DEFAULT_INITIAL_SCORE),
        }

    overall = float(rating.overall_score)
    return {
        'overall_score': overall,
        'quality_score': float(rating.quality_score),
        'service_score': float(rating.service_score),
        'logistics_score': float(rating.logistics_score),
        'total_ratings': rating.total_ratings,
        'rating_label': get_rating_label(overall),
    }


def sync_user_rating_from_product_review(review) -> UserRating | None:
    """Map product review into tenant user rating."""
    product = review.product
    if not product or not product.tenant_id:
        return None

    score = max(1, min(5, int(review.rating or 5)))
    defaults = {
        'tenant_id': product.tenant_id,
        'customer_id': review.customer_id,
        'order_id': review.order_id,
        'quality_score': score,
        'service_score': score,
        'logistics_score': score,
        'content': review.content or '',
    }
    user_rating, _ = UserRating.objects.update_or_create(
        product_review=review,
        defaults=defaults,
    )

    update_shop_score(product.tenant)
    return user_rating


def detect_rating_alerts(days: int = 1) -> list[dict[str, Any]]:
    """Detect suspicious rating bursts."""
    since = timezone.now() - timezone.timedelta(days=days)
    rows = (
        UserRating.objects.filter(created_at__gte=since)
        .values('tenant_id', 'tenant__name')
        .annotate(
            total=Count('id'),
            five_star=Count('id', filter=Q(quality_score=5, service_score=5, logistics_score=5)),
            one_star=Count('id', filter=Q(quality_score=1) | Q(service_score=1) | Q(logistics_score=1)),
        )
        .filter(Q(total__gte=10) | Q(five_star__gte=8) | Q(one_star__gte=5))
        .order_by('-total')[:50]
    )
    alerts = []
    for row in rows:
        alerts.append(
            {
                'tenant_id': row['tenant_id'],
                'tenant_name': row['tenant__name'],
                'total': row['total'],
                'five_star': row['five_star'],
                'one_star': row['one_star'],
            },
        )
    return alerts
