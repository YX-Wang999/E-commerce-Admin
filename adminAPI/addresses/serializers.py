"""Address serializers."""

from rest_framework import serializers

from addresses.models import Address


class AddressSerializer(serializers.ModelSerializer):
    """Address read/write serializer."""

    full_address = serializers.CharField(read_only=True)

    class Meta:
        model = Address
        fields = [
            'id', 'name', 'phone', 'province', 'city', 'district', 'detail',
            'is_default', 'full_address', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'full_address', 'created_at', 'updated_at']
