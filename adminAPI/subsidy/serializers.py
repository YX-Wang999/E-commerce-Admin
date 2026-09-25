"""Subsidy serializers."""

from rest_framework import serializers

from common.media_utils import file_field_url
from subsidy.models import SubsidyOrder, SubsidyPolicy, SubsidyProduct


class SubsidyPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubsidyPolicy
        fields = [
            'id',
            'name',
            'description',
            'subsidy_type',
            'subsidy_value',
            'max_subsidy',
            'region',
            'category',
            'is_active',
            'start_time',
            'end_time',
            'created_at',
            'updated_at',
        ]


class SubsidyProductSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(
        source='product.price',
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    product_image = serializers.SerializerMethodField()
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    policy_name = serializers.CharField(source='policy.name', read_only=True)
    filing_status_label = serializers.CharField(source='get_filing_status_display', read_only=True)

    class Meta:
        model = SubsidyProduct
        fields = [
            'id',
            'product',
            'product_name',
            'product_price',
            'product_image',
            'tenant',
            'tenant_name',
            'policy',
            'policy_name',
            'region',
            'category',
            'filing_status',
            'filing_status_label',
            'subsidy_amount',
            'filing_submitted_at',
            'filing_reject_reason',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'tenant',
            'filing_status',
            'subsidy_amount',
            'filing_submitted_at',
            'filing_reject_reason',
        ]

    def get_product_image(self, obj) -> str:
        product = obj.product
        if not product:
            return ''
        return file_field_url(product.image, getattr(product, 'updated_at', None))


class SubsidyOrderSerializer(serializers.ModelSerializer):
    order_no = serializers.CharField(source='order.order_no', read_only=True)
    product_name = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source='order.customer.nickname', read_only=True, default='')
    government_status_label = serializers.CharField(source='get_government_status_display', read_only=True)

    class Meta:
        model = SubsidyOrder
        fields = [
            'id',
            'order',
            'order_no',
            'product_name',
            'customer_name',
            'tenant',
            'sn_code',
            'imei_code',
            'government_status',
            'government_status_label',
            'reported_at',
            'fail_reason',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['tenant', 'government_status', 'reported_at', 'fail_reason']

    def get_product_name(self, obj) -> str:
        item = obj.order.items.first()
        return item.product_name if item else ''


class SellerSubsidyFilingSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    policy_id = serializers.IntegerField(required=False)
    region = serializers.CharField(max_length=64)
    category = serializers.CharField(max_length=64)


class SubsidyOrderCodesSerializer(serializers.Serializer):
    sn_code = serializers.CharField(max_length=100, required=False, allow_blank=True)
    imei_code = serializers.CharField(max_length=200, required=False, allow_blank=True)

    def validate(self, attrs):
        if not (attrs.get('sn_code') or '').strip() and not (attrs.get('imei_code') or '').strip():
            raise serializers.ValidationError('请至少填写 SN 码或 IMEI 码')
        return attrs


class GovernmentFilingSyncSerializer(serializers.Serializer):
    """Simulate government filing status callback (platform monitoring only)."""

    filing_status = serializers.ChoiceField(
        choices=[
            SubsidyProduct.FILING_SUBMITTED,
            SubsidyProduct.FILING_APPROVED,
            SubsidyProduct.FILING_REJECTED,
        ],
    )
    filing_reject_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs['filing_status'] == SubsidyProduct.FILING_REJECTED:
            if not (attrs.get('filing_reject_reason') or '').strip():
                raise serializers.ValidationError({'filing_reject_reason': '驳回时需填写原因'})
        return attrs
