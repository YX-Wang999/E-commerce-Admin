"""Customer serializers."""

from rest_framework import serializers

from customers.models import Customer


class CustomerProfileSerializer(serializers.ModelSerializer):
    """Mall customer profile (no password)."""

    display_name = serializers.CharField(read_only=True)
    identity_verified = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            'id', 'phone', 'email', 'nickname', 'name', 'real_name', 'display_name', 'avatar',
            'level', 'points', 'identity_verified', 'is_active', 'registered_at', 'created_at',
        ]
        read_only_fields = [
            'id', 'phone', 'level', 'points', 'is_active', 'registered_at', 'created_at',
        ]

    def get_identity_verified(self, obj: Customer) -> bool:
        return bool((obj.real_name or '').strip())


class CustomerSerializer(serializers.ModelSerializer):
    """Admin customer management serializer."""

    display_name = serializers.CharField(read_only=True)
    member_level_name = serializers.SerializerMethodField()
    growth_points = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = [
            'id', 'phone', 'email', 'nickname', 'name', 'display_name', 'avatar',
            'level', 'member_level_name', 'growth_points', 'points', 'is_active',
            'registered_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'phone', 'registered_at', 'created_at', 'updated_at', 'password']

    def get_member_level_name(self, obj) -> str:
        profile = getattr(obj, 'member_profile', None)
        if profile and profile.current_level_id:
            return profile.current_level.name
        return ''

    def get_growth_points(self, obj) -> int:
        profile = getattr(obj, 'member_profile', None)
        return profile.growth_points if profile else 0
