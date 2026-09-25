"""Complaint serializers."""

from rest_framework import serializers

from chat.models import Complaint, ComplaintMessage


class ComplaintMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintMessage
        fields = [
            'id',
            'sender_type',
            'sender_id',
            'content',
            'attachments',
            'is_internal',
            'created_at',
        ]
        read_only_fields = fields


class ComplaintSerializer(serializers.ModelSerializer):
    complaint_no = serializers.CharField(read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    customer_name = serializers.CharField(source='customer.display_name', read_only=True)
    order_no = serializers.CharField(source='order.order_no', read_only=True, default='')
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    platform_decision_display = serializers.CharField(
        source='get_platform_decision_display',
        read_only=True,
    )
    reviewer_name = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()

    class Meta:
        model = Complaint
        fields = [
            'id',
            'complaint_no',
            'customer',
            'customer_name',
            'tenant',
            'tenant_name',
            'order',
            'order_no',
            'category',
            'category_display',
            'title',
            'content',
            'attachments',
            'status',
            'status_display',
            'merchant_reply',
            'merchant_replied_at',
            'customer_satisfied',
            'customer_reviewed_at',
            'platform_decision',
            'platform_decision_display',
            'platform_remark',
            'platform_reply',
            'reviewed_by',
            'reviewer_name',
            'platform_reviewed_at',
            'resolution',
            'resolved_at',
            'messages',
            'created_at',
            'updated_at',
        ]

    def get_reviewer_name(self, obj: Complaint) -> str:
        if not obj.reviewed_by_id:
            return ''
        return obj.reviewed_by.nickname or obj.reviewed_by.username

    def get_messages(self, obj: Complaint):
        request = self.context.get('request')
        include_internal = False
        if request and getattr(request, 'user', None) and request.user.is_authenticated:
            from complaints.permissions import user_is_platform_complaint_staff

            include_internal = user_is_platform_complaint_staff(request.user)
        queryset = obj.messages.all()
        if not include_internal:
            queryset = queryset.filter(is_internal=False)
        return ComplaintMessageSerializer(queryset, many=True).data


class ComplaintCreateSerializer(serializers.Serializer):
    tenant_id = serializers.IntegerField()
    order_id = serializers.IntegerField()
    category = serializers.ChoiceField(choices=Complaint.CATEGORY_CHOICES)
    title = serializers.CharField(max_length=200)
    content = serializers.CharField(max_length=5000)
    attachments = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False,
        default=list,
    )


class ComplaintMessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=5000)
    attachments = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False,
        default=list,
    )
    is_internal = serializers.BooleanField(required=False, default=False)


class MerchantReplySerializer(serializers.Serializer):
    content = serializers.CharField(max_length=5000)
    attachments = serializers.ListField(
        child=serializers.CharField(max_length=500),
        required=False,
        default=list,
    )
    mark_processed = serializers.BooleanField(required=False, default=False)


class CustomerReviewSerializer(serializers.Serializer):
    satisfied = serializers.BooleanField()
    comment = serializers.CharField(max_length=2000, required=False, allow_blank=True, default='')


class RequestPlatformSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=2000, required=False, allow_blank=True, default='')


class PlatformReviewSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=Complaint.DECISION_CHOICES)
    platform_remark = serializers.CharField(max_length=5000)
    resolution = serializers.CharField(max_length=5000, required=False, allow_blank=True, default='')
    internal_note = serializers.CharField(max_length=5000, required=False, allow_blank=True, default='')
