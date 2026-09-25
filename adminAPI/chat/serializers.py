"""Chat serializers."""

from rest_framework import serializers

from chat.models import Conversation, Message
from chat.services import get_sender_display_name, message_is_platform_staff


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    is_staff = serializers.SerializerMethodField()
    is_platform_staff = serializers.SerializerMethodField()
    sender = serializers.IntegerField(source='sender_staff_id', read_only=True, allow_null=True)
    sender_customer = serializers.IntegerField(source='sender_user_id', read_only=True, allow_null=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'conversation',
            'sender_type',
            'sender',
            'sender_customer',
            'sender_name',
            'is_staff',
            'is_platform_staff',
            'content',
            'is_sensitive',
            'read_at',
            'created_at',
        ]
        read_only_fields = fields

    def get_sender_name(self, obj: Message) -> str:
        return get_sender_display_name(obj)

    def get_is_staff(self, obj: Message) -> bool:
        return obj.is_staff

    def get_is_platform_staff(self, obj: Message) -> bool:
        return message_is_platform_staff(obj)


class ConversationSerializer(serializers.ModelSerializer):
    customer = serializers.IntegerField(source='user_id', read_only=True, allow_null=True)
    customer_name = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    tenant_name = serializers.CharField(source='tenant.name', read_only=True, allow_null=True)
    conversation_type_display = serializers.CharField(source='get_conversation_type_display', read_only=True)
    user_unread_count = serializers.IntegerField(source='unread_count_user', read_only=True)
    staff_unread_count = serializers.IntegerField(source='unread_count_staff', read_only=True)
    assigned_to_name = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'conversation_type',
            'conversation_type_display',
            'tenant',
            'tenant_name',
            'customer',
            'customer_name',
            'customer_phone',
            'complaint',
            'assigned_to',
            'assigned_to_name',
            'status',
            'user_unread_count',
            'staff_unread_count',
            'unread_count',
            'last_message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

    def get_customer_name(self, obj: Conversation) -> str:
        if obj.is_merchant_conversation and obj.tenant_id:
            return obj.tenant.name
        if obj.user_id:
            return obj.user.display_name
        return '平台会话'

    def get_customer_phone(self, obj: Conversation) -> str:
        if obj.user_id:
            return obj.user.phone or ''
        if obj.tenant_id:
            return obj.tenant.contact_phone or ''
        return ''

    def get_assigned_to_name(self, obj: Conversation) -> str | None:
        if not obj.assigned_to:
            return None
        return obj.assigned_to.nickname or obj.assigned_to.username

    def get_last_message(self, obj: Conversation) -> dict | None:
        message = obj.messages.order_by('-created_at').first()
        if not message:
            return None
        return {
            'content': message.content[:80],
            'is_staff': message.is_staff,
            'is_sensitive': message.is_sensitive,
            'created_at': message.created_at.isoformat(),
        }

    def get_unread_count(self, obj: Conversation) -> int:
        request = self.context.get('request')
        if not request:
            return 0
        from chat.permissions import is_chat_staff

        if getattr(request, 'customer', None):
            return obj.unread_count_user
        if request.user.is_authenticated and is_chat_staff(request.user):
            return obj.unread_count_staff
        if request.user.is_authenticated and getattr(request, 'tenant', None):
            return obj.unread_count_staff
        return 0
