"""Logistics serializers."""

from rest_framework import serializers

from logistics.models import Logistics


class LogisticsTraceSerializer(serializers.Serializer):
    time = serializers.CharField(allow_blank=True, required=False)
    content = serializers.CharField(allow_blank=True, required=False)
    status = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    area = serializers.CharField(allow_blank=True, required=False)


class LogisticsSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Logistics
        fields = [
            'id',
            'express_company',
            'express_code',
            'tracking_number',
            'status',
            'status_label',
            'traces',
            'picked_at',
            'delivered_at',
            'last_trace_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields
