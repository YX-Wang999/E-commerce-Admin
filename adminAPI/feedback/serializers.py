"""Customer feedback serializers."""

from django.utils import timezone
from rest_framework import serializers

from customers.models import Customer
from feedback.models import CustomerFeedback


class CustomerFeedbackSerializer(serializers.ModelSerializer):
    """Feedback read serializer."""

    handler_name = serializers.SerializerMethodField()
    feedback_type_label = serializers.CharField(source='get_feedback_type_display', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = CustomerFeedback
        fields = [
            'id',
            'customer',
            'tenant',
            'nickname',
            'phone',
            'feedback_type',
            'feedback_type_label',
            'content',
            'images',
            'status',
            'status_label',
            'handler',
            'handler_name',
            'handler_remark',
            'created_at',
            'handled_at',
        ]
        read_only_fields = fields

    def get_handler_name(self, obj: CustomerFeedback) -> str:
        """Return handler display name."""
        if obj.handler_id is None:
            return ''
        return obj.handler.nickname or obj.handler.username


class CustomerFeedbackReplySerializer(serializers.Serializer):
    """Reply and status update serializer."""

    status = serializers.ChoiceField(choices=CustomerFeedback.STATUS_CHOICES)
    handler_remark = serializers.CharField(max_length=2000, allow_blank=True, required=False)


class CustomerFeedbackSubmitSerializer(serializers.ModelSerializer):
    """Public mall submission serializer."""

    class Meta:
        model = CustomerFeedback
        fields = [
            'nickname',
            'phone',
            'feedback_type',
            'content',
            'images',
            'tenant_id',
        ]

    tenant_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)

    def validate_tenant_id(self, value):
        if value is None:
            return value
        from tenants.models import Tenant

        if not Tenant.objects.filter(pk=value, status=Tenant.STATUS_ACTIVE, is_active=True).exists():
            raise serializers.ValidationError('商户不存在或未入驻')
        return value

    def validate_content(self, value: str) -> str:
        """Limit content length."""
        if len(value) > 500:
            raise serializers.ValidationError('留言内容不能超过 500 字')
        return value

    def validate_images(self, value: list) -> list:
        """Limit image count."""
        if len(value) > 3:
            raise serializers.ValidationError('最多上传 3 张图片')
        return value

    def create(self, validated_data: dict) -> CustomerFeedback:
        """Create feedback and link customer by phone when possible."""
        tenant_id = validated_data.pop('tenant_id', None)
        phone = validated_data.get('phone', '').strip()
        customer = self.context.get('customer')
        if customer is None and phone:
            customer = Customer.objects.filter(phone=phone, is_active=True).first()
        tenant = None
        if tenant_id:
            from tenants.models import Tenant

            tenant = Tenant.objects.filter(pk=tenant_id, status=Tenant.STATUS_ACTIVE, is_active=True).first()
        instance = CustomerFeedback.objects.create(
            customer=customer,
            tenant=tenant,
            **validated_data,
        )
        if tenant_id:
            self._notify_tenant_feedback(instance)
        return instance

    def _notify_tenant_feedback(self, feedback: CustomerFeedback) -> None:
        if not feedback.tenant_id:
            return
        try:
            from notification.models import Notification
            from notification.services import create_notification

            create_notification(
                recipient_type=Notification.RECIPIENT_TENANT,
                recipient_id=feedback.tenant_id,
                title='客户留言',
                content=(feedback.content or '')[:120],
                notification_type=Notification.TYPE_SYSTEM,
                related_url='/orders/refunds',
                related_id=feedback.id,
                level='info',
            )
        except Exception:
            pass
