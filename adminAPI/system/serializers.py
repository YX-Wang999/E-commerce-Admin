"""System setting serializers."""

from rest_framework import serializers

from system.models import SystemSetting


class SystemSettingSerializer(serializers.ModelSerializer):
    """System setting serializer."""

    class Meta:
        model = SystemSetting
        fields = [
            'id',
            'key',
            'value',
            'value_type',
            'description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
