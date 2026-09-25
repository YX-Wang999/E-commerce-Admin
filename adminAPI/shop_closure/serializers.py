"""Shop closure serializers."""

from rest_framework import serializers

from shop_closure.models import ClosureApplication, ClosureChecklist, ClosureNotification


class ClosureChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClosureChecklist
        fields = ['id', 'code', 'item', 'is_completed', 'completed_at', 'remark']


class ClosureNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClosureNotification
        fields = ['id', 'recipient', 'channel', 'content', 'sent_at', 'is_delivered']


class ClosureApplicationSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_code = serializers.CharField(source='tenant.code', read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()
    checklist = ClosureChecklistSerializer(many=True, read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ClosureApplication
        fields = [
            'id',
            'tenant',
            'tenant_name',
            'tenant_code',
            'reason',
            'detail',
            'attachments',
            'status',
            'status_label',
            'reviewed_by',
            'reviewed_by_name',
            'reviewed_at',
            'reject_reason',
            'notice_start_at',
            'notice_end_at',
            'notice_days',
            'completed_at',
            'data_exported_at',
            'data_export_url',
            'checklist',
            'created_at',
            'updated_at',
        ]

    def get_reviewed_by_name(self, obj: ClosureApplication) -> str:
        if not obj.reviewed_by:
            return ''
        return obj.reviewed_by.nickname or obj.reviewed_by.username


class ClosureApplySerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=200)
    detail = serializers.CharField(required=False, allow_blank=True, default='')
    attachments = serializers.ListField(child=serializers.JSONField(), required=False, default=list)


class ClosureReviewSerializer(serializers.Serializer):
    reject_reason = serializers.CharField(required=False, allow_blank=True, default='')
    notice_days = serializers.IntegerField(required=False, min_value=7, max_value=30, default=15)


class ClosureConditionSerializer(serializers.Serializer):
    code = serializers.CharField()
    item = serializers.CharField()
    is_completed = serializers.BooleanField()
    remark = serializers.CharField(allow_blank=True)
    count = serializers.JSONField()
