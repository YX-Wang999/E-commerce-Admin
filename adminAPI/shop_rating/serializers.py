"""Shop rating serializers."""

from rest_framework import serializers

from shop_rating.models import RatingAdjustmentRequest, ShopRating, UserRating


class ShopRatingSerializer(serializers.ModelSerializer):
    rating_label = serializers.SerializerMethodField()

    class Meta:
        model = ShopRating
        fields = [
            'overall_score',
            'quality_score',
            'service_score',
            'logistics_score',
            'total_ratings',
            'total_orders',
            'completed_orders',
            'refund_orders',
            'rating_label',
            'updated_at',
        ]
        read_only_fields = fields

    def get_rating_label(self, obj: ShopRating) -> str:
        from shop_rating.services import get_rating_label

        return get_rating_label(obj.overall_score)


class UserRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRating
        fields = [
            'id',
            'quality_score',
            'service_score',
            'logistics_score',
            'content',
            'images',
            'is_anonymous',
            'created_at',
        ]
        read_only_fields = fields


class RatingAdjustmentRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RatingAdjustmentRequest
        fields = [
            'id',
            'current_score',
            'requested_score',
            'reason',
            'status',
            'review_note',
            'created_at',
            'reviewed_at',
        ]
        read_only_fields = ['id', 'current_score', 'status', 'review_note', 'created_at', 'reviewed_at']


class RatingAdjustmentApplySerializer(serializers.Serializer):
    requested_score = serializers.DecimalField(max_digits=3, decimal_places=1)
    reason = serializers.CharField(max_length=200)


class RatingAdjustmentReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['approved', 'rejected'])
    review_note = serializers.CharField(max_length=200, required=False, allow_blank=True, default='')
