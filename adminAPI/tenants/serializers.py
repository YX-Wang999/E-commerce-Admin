"""Tenant API serializers."""

import re

from rest_framework import serializers

from accounts.models import Department
from tenants.models import (
    Tenant,
    TenantActionLog,
    TenantStaff,
    TenantSuspensionLog,
    TenantAppeal,
    TenantAppealMessage,
    TenantInboxMessage,
    TenantChangeLog,
)
from tenants.change_constants import FIELD_LABELS
from tenants.change_services import get_tenant_pending_fields
from tenants.name_rules import validate_tenant_name

PHONE_PATTERN = re.compile(r'^1[3-9]\d{9}$')


class TenantSuspensionLogSerializer(serializers.ModelSerializer):
    operator_name = serializers.SerializerMethodField()

    class Meta:
        model = TenantSuspensionLog
        fields = ['id', 'action', 'reason', 'detail', 'operator', 'operator_name', 'created_at']
        read_only_fields = fields

    def get_operator_name(self, obj: TenantSuspensionLog) -> str:
        if not obj.operator_id:
            return '系统'
        return obj.operator.nickname or obj.operator.username


class TenantAppealSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_code = serializers.CharField(source='tenant.code', read_only=True)
    tenant_phone = serializers.CharField(source='tenant.contact_phone', read_only=True)
    operator_name = serializers.SerializerMethodField()

    class Meta:
        model = TenantAppeal
        fields = [
            'id',
            'tenant',
            'tenant_name',
            'tenant_code',
            'tenant_phone',
            'title',
            'content',
            'attachments',
            'status',
            'reply',
            'operator',
            'operator_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'tenant',
            'tenant_name',
            'tenant_code',
            'tenant_phone',
            'status',
            'reply',
            'operator',
            'operator_name',
            'created_at',
            'updated_at',
        ]

    def get_operator_name(self, obj: TenantAppeal) -> str:
        if not obj.operator_id:
            return ''
        return obj.operator.nickname or obj.operator.username


class TenantAppealCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantAppeal
        fields = ['title', 'content', 'attachments']


class TenantAppealReplySerializer(serializers.Serializer):
    reply = serializers.CharField(max_length=5000)
    status = serializers.ChoiceField(choices=[
        TenantAppeal.STATUS_RESOLVED,
        TenantAppeal.STATUS_REJECTED,
        TenantAppeal.STATUS_PROCESSING,
    ])


class TenantAppealMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = TenantAppealMessage
        fields = ['id', 'sender_type', 'sender_name', 'content', 'created_at']
        read_only_fields = fields

    def get_sender_name(self, obj: TenantAppealMessage) -> str:
        if obj.sender_type == TenantAppealMessage.SENDER_PLATFORM:
            if obj.sender_user_id:
                return obj.sender_user.nickname or obj.sender_user.username
            return '平台客服'
        if obj.sender_user_id:
            return obj.sender_user.nickname or obj.sender_user.username
        return '商户'


class TenantInboxMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantInboxMessage
        fields = [
            'id',
            'message_type',
            'title',
            'content',
            'is_read',
            'appeal_id',
            'created_at',
        ]
        read_only_fields = fields


class SellerAppealDetailSerializer(serializers.ModelSerializer):
    messages = TenantAppealMessageSerializer(many=True, read_only=True)

    class Meta:
        model = TenantAppeal
        fields = [
            'id',
            'title',
            'content',
            'status',
            'reply',
            'created_at',
            'updated_at',
            'messages',
        ]
        read_only_fields = fields


class TenantActionLogSerializer(serializers.ModelSerializer):
    operator_name = serializers.SerializerMethodField()

    class Meta:
        model = TenantActionLog
        fields = ['id', 'action', 'operator', 'operator_name', 'remark', 'created_at']
        read_only_fields = fields

    def get_operator_name(self, obj: TenantActionLog) -> str:
        if not obj.operator_id:
            return '系统'
        return obj.operator.nickname or obj.operator.username


class TenantSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    approved_by_name = serializers.SerializerMethodField()
    pending_fields = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            'id',
            'name',
            'code',
            'logo',
            'contact_name',
            'contact_phone',
            'contact_email',
            'legal_person',
            'business_license',
            'address',
            'description',
            'pending_name',
            'pending_contact_phone',
            'pending_contact_email',
            'pending_contact_name',
            'pending_legal_person',
            'pending_business_license',
            'pending_fields',
            'department',
            'department_name',
            'status',
            'applied_at',
            'approved_at',
            'approved_by',
            'approved_by_name',
            'config',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'code',
            'applied_at',
            'approved_at',
            'approved_by',
            'pending_name',
            'pending_contact_phone',
            'pending_contact_email',
            'pending_contact_name',
            'pending_legal_person',
            'pending_business_license',
            'pending_fields',
            'created_at',
            'updated_at',
        ]

    def get_pending_fields(self, obj: Tenant) -> dict[str, str]:
        return get_tenant_pending_fields(obj)

    def validate_contact_phone(self, value: str) -> str:
        phone = (value or '').strip()
        if not PHONE_PATTERN.match(phone):
            raise serializers.ValidationError('请输入正确的手机号')
        queryset = Tenant.objects.filter(contact_phone=phone)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('该联系电话已被其他商户使用')
        return phone

    def validate_name(self, value: str) -> str:
        name = (value or '').strip()
        format_error = validate_tenant_name(name)
        if format_error:
            raise serializers.ValidationError(format_error)
        queryset = Tenant.objects.filter(name__iexact=name)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        duplicate = queryset.first()
        if duplicate and duplicate.status != Tenant.STATUS_ACTIVE:
            raise serializers.ValidationError('该店铺名称已被使用')
        return name

    def validate_contact_name(self, value: str) -> str:
        contact_name = (value or '').strip()
        queryset = Tenant.objects.filter(contact_name__iexact=contact_name)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('该联系人已被其他商户使用')
        return contact_name

    def validate_code(self, value: str) -> str:
        if self.instance is not None and value != self.instance.code:
            raise serializers.ValidationError('商户编码不可修改')
        return value

    def validate(self, attrs):
        if self.instance is None:
            attrs.pop('code', None)
        else:
            attrs['code'] = self.instance.code
        return attrs

    def get_approved_by_name(self, obj: Tenant) -> str | None:
        if not obj.approved_by_id:
            return None
        return obj.approved_by.nickname or obj.approved_by.username

    def validate_department(self, value: Department | None) -> Department | None:
        if value is not None and not value.is_active:
            raise serializers.ValidationError('所选部门已禁用')
        return value


class TenantDetailSerializer(TenantSerializer):
    action_logs = TenantActionLogSerializer(many=True, read_only=True)
    suspension_logs = TenantSuspensionLogSerializer(many=True, read_only=True)

    class Meta(TenantSerializer.Meta):
        fields = [*TenantSerializer.Meta.fields, 'action_logs', 'suspension_logs']


class TenantStaffSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = TenantStaff
        fields = [
            'id',
            'tenant',
            'user',
            'user_username',
            'role',
            'permissions',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['created_at']


class TenantChangeLogSerializer(serializers.ModelSerializer):
    field_label = serializers.SerializerMethodField()
    operator_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)

    class Meta:
        model = TenantChangeLog
        fields = [
            'id',
            'tenant',
            'tenant_name',
            'field',
            'field_label',
            'old_value',
            'new_value',
            'status',
            'operator',
            'operator_name',
            'operator_type',
            'reviewed_by',
            'reviewed_by_name',
            'reviewed_at',
            'review_remark',
            'created_at',
        ]
        read_only_fields = fields

    def get_field_label(self, obj: TenantChangeLog) -> str:
        return FIELD_LABELS.get(obj.field, obj.field)

    def get_operator_name(self, obj: TenantChangeLog) -> str:
        if not obj.operator_id:
            return '商户'
        return obj.operator.nickname or obj.operator.username

    def get_reviewed_by_name(self, obj: TenantChangeLog) -> str:
        if not obj.reviewed_by_id:
            return ''
        return obj.reviewed_by.nickname or obj.reviewed_by.username


class TenantChangeReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    remark = serializers.CharField(required=False, allow_blank=True, max_length=500)


class SellerTenantProfileUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True, max_length=100)
    contact_name = serializers.CharField(required=False, allow_blank=True, max_length=50)
    contact_phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    contact_email = serializers.EmailField(required=False, allow_blank=True)
    legal_person = serializers.CharField(required=False, allow_blank=True, max_length=50)
    business_license = serializers.URLField(required=False, allow_blank=True, max_length=500)
    address = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    logo = serializers.URLField(required=False, allow_blank=True, max_length=200)
    config = serializers.JSONField(required=False)


class PublicTenantSerializer(serializers.ModelSerializer):
    """Storefront tenant card with lightweight stats."""

    intro = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()
    rating_label = serializers.SerializerMethodField()
    quality_score = serializers.SerializerMethodField()
    service_score = serializers.SerializerMethodField()
    logistics_score = serializers.SerializerMethodField()
    sold_count = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    closure_state = serializers.SerializerMethodField()
    closure_notice_end_at = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            'id',
            'name',
            'code',
            'logo',
            'description',
            'status',
            'intro',
            'rating',
            'rating_count',
            'rating_label',
            'quality_score',
            'service_score',
            'logistics_score',
            'sold_count',
            'product_count',
            'closure_state',
            'closure_notice_end_at',
        ]
        read_only_fields = fields

    def get_closure_state(self, obj: Tenant) -> str:
        from shop_closure.services import tenant_closure_state

        return tenant_closure_state(obj)['state']

    def get_closure_notice_end_at(self, obj: Tenant) -> str | None:
        from shop_closure.services import tenant_closure_state

        return tenant_closure_state(obj)['notice_end_at']

    def get_intro(self, obj: Tenant) -> str:
        if (obj.description or '').strip():
            return obj.description.strip()
        config = obj.config or {}
        return str(config.get('intro') or obj.address or '')

    def get_rating(self, obj: Tenant) -> float:
        from shop_rating.services import get_tenant_rating_display

        return get_tenant_rating_display(obj.id)['overall_score']

    def get_rating_count(self, obj: Tenant) -> int:
        from shop_rating.services import get_tenant_rating_display

        return get_tenant_rating_display(obj.id)['total_ratings']

    def get_rating_label(self, obj: Tenant) -> str:
        from shop_rating.services import get_tenant_rating_display

        return get_tenant_rating_display(obj.id)['rating_label']

    def get_quality_score(self, obj: Tenant) -> float:
        from shop_rating.services import get_tenant_rating_display

        return get_tenant_rating_display(obj.id)['quality_score']

    def get_service_score(self, obj: Tenant) -> float:
        from shop_rating.services import get_tenant_rating_display

        return get_tenant_rating_display(obj.id)['service_score']

    def get_logistics_score(self, obj: Tenant) -> float:
        from shop_rating.services import get_tenant_rating_display

        return get_tenant_rating_display(obj.id)['logistics_score']

    def get_sold_count(self, obj: Tenant) -> int:
        from django.db.models import Sum

        from orders.models import Order, OrderItem

        total = OrderItem.objects.filter(
            product__tenant_id=obj.id,
            order__status__in=[
                Order.STATUS_PAID,
                Order.STATUS_SHIPPED,
                Order.STATUS_COMPLETED,
            ],
        ).aggregate(total=Sum('quantity'))['total']
        return int(total or 0)

    def get_product_count(self, obj: Tenant) -> int:
        from products.models import Product

        return Product.objects.filter(
            tenant_id=obj.id,
            is_active=True,
            status=Product.STATUS_ON_SALE,
        ).count()
