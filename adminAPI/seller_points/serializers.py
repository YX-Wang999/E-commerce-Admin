"""Serializers for seller points."""

from rest_framework import serializers

from seller_points.models import SellerPointsAccount, SellerPointsRule, SellerPointsTransaction


class SellerPointsRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerPointsRule
        fields = [
            'earn_rate',
            'max_earn_per_order',
            'redeem_rate',
            'max_redeem_rate',
            'expire_days',
            'points_name',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class SellerPointsAccountSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)

    class Meta:
        model = SellerPointsAccount
        fields = [
            'id',
            'customer',
            'customer_name',
            'customer_phone',
            'balance',
            'total_earned',
            'total_spent',
            'expire_at',
            'updated_at',
        ]


class SellerPointsTransactionSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    trans_type_display = serializers.CharField(source='get_trans_type_display', read_only=True)

    class Meta:
        model = SellerPointsTransaction
        fields = [
            'id',
            'customer',
            'customer_name',
            'amount',
            'balance_after',
            'trans_type',
            'trans_type_display',
            'source_id',
            'description',
            'created_at',
        ]


class SellerPointsAdjustSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    amount = serializers.IntegerField()
    description = serializers.CharField(required=False, allow_blank=True, default='')
