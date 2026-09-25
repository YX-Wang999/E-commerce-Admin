"""Complaint serializers."""

from rest_framework import serializers

from chat.models import Complaint


class ComplaintSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    customer_name = serializers.CharField(source='customer.display_name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reviewer_name = serializers.SerializerMethodField()

    class Meta:
        model = Complaint
        fields = [
            'id',
            'customer',
            'customer_name',
            'tenant',
            'tenant_name',
            'order',
            'category',
            'category_display',
            'content',
            'attachments',
            'status',
            'status_display',
            'platform_reply',
            'reviewed_by',
            'reviewer_name',
            'created_at',
            'resolved_at',
        ]
        read_only_fields = [
            'id',
            'customer',
            'customer_name',
            'tenant_name',
            'status',
            'status_display',
            'platform_reply',
            'reviewed_by',
            'reviewer_name',
            'created_at',
            'resolved_at',
        ]

    def get_reviewer_name(self, obj: Complaint) -> str:
        if not obj.reviewed_by_id:
            return ''
        return obj.reviewed_by.nickname or obj.reviewed_by.username


class ComplaintCreateSerializer(serializers.ModelSerializer):
    tenant_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Complaint
        fields = ['tenant_id', 'order', 'category', 'content', 'attachments']

    def validate_tenant_id(self, value: int) -> int:
        from tenants.models import Tenant

        if not Tenant.objects.filter(pk=value, status=Tenant.STATUS_ACTIVE).exists():
            raise serializers.ValidationError('商户不存在或未入驻')
        return value


class ComplaintReplySerializer(serializers.Serializer):
    platform_reply = serializers.CharField(max_length=5000)
    status = serializers.ChoiceField(choices=[
        Complaint.STATUS_MERCHANT_PROCESSING,
        Complaint.STATUS_PLATFORM_REVIEWING,
        Complaint.STATUS_RESOLVED,
        Complaint.STATUS_REJECTED,
    ])
