"""Membership serializers."""

from rest_framework import serializers

from membership.models import GrowthLog, MemberLevel, MemberProfile


class MemberLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberLevel
        fields = [
            'id', 'level', 'name', 'min_points', 'discount_rate',
            'points_multiplier', 'description', 'sort_order', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GrowthLogSerializer(serializers.ModelSerializer):
    log_type_label = serializers.CharField(source='get_log_type_display', read_only=True)

    class Meta:
        model = GrowthLog
        fields = [
            'id', 'amount', 'balance_after', 'log_type', 'log_type_label',
            'description', 'created_at',
        ]


class MemberProfileAdminSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.display_name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    level_name = serializers.CharField(source='current_level.name', read_only=True)
    level_value = serializers.IntegerField(source='current_level.level', read_only=True)

    class Meta:
        model = MemberProfile
        fields = [
            'id', 'customer', 'customer_name', 'customer_phone',
            'current_level', 'level_name', 'level_value',
            'growth_points', 'checkin_streak', 'total_checkins',
            'last_checkin_date', 'level_upgraded_at', 'updated_at',
        ]
        read_only_fields = fields
