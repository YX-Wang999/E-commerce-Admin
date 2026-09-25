"""Points serializers."""

import re
from decimal import Decimal

from rest_framework import serializers

from customers.models import Customer
from points.models import PointsAccount, PointsRule, PointsTransaction


class PointsAccountSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)

    class Meta:
        model = PointsAccount
        fields = [
            'id', 'customer', 'customer_name', 'customer_phone',
            'balance', 'total_earned', 'total_spent', 'updated_at',
        ]


class PointsTransactionSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    trans_type_label = serializers.CharField(source='get_trans_type_display', read_only=True)

    class Meta:
        model = PointsTransaction
        fields = [
            'id', 'customer', 'customer_name', 'customer_phone',
            'amount', 'balance_after', 'trans_type', 'trans_type_label',
            'source', 'description', 'created_at',
        ]


class PointsRuleSerializer(serializers.ModelSerializer):
    points_value = serializers.SerializerMethodField()

    class Meta:
        model = PointsRule
        fields = [
            'id', 'code', 'name', 'description', 'rule_type',
            'default_value', 'current_value', 'min_value', 'max_value',
            'is_active', 'is_system', 'sort_order', 'trigger_config',
            'points_value', 'created_at', 'updated_at',
        ]

    def get_points_value(self, obj: PointsRule) -> int:
        return int(obj.current_value or 0)


class PointsRuleWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointsRule
        fields = [
            'id', 'code', 'name', 'description', 'rule_type',
            'default_value', 'current_value', 'min_value', 'max_value',
            'is_active', 'sort_order', 'trigger_config',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields['code'].read_only = True
            if self.instance.is_system:
                self.fields['rule_type'].read_only = True

    def validate_code(self, value: str) -> str:
        code = (value or '').strip().lower()
        if not code:
            raise serializers.ValidationError('规则编码不能为空')
        if not re.fullmatch(r'[a-z][a-z0-9_]{1,48}', code):
            raise serializers.ValidationError('编码仅支持小写字母、数字和下划线，且以字母开头')
        return code

    def validate(self, attrs):
        instance = self.instance
        current = attrs.get('current_value', getattr(instance, 'current_value', None))
        min_value = attrs.get('min_value', getattr(instance, 'min_value', None))
        max_value = attrs.get('max_value', getattr(instance, 'max_value', None))
        if current is not None:
            value = Decimal(str(current))
            if min_value is not None and value < Decimal(str(min_value)):
                raise serializers.ValidationError({'current_value': '不能小于最小值'})
            if max_value is not None and value > Decimal(str(max_value)):
                raise serializers.ValidationError({'current_value': '不能大于最大值'})
        return attrs


class PointsAdjustSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    amount = serializers.IntegerField()
    description = serializers.CharField(max_length=255, allow_blank=True, required=False)

    def validate_customer_id(self, value: int) -> int:
        if not Customer.objects.filter(pk=value, is_active=True).exists():
            raise serializers.ValidationError('会员不存在')
        return value

    def validate_amount(self, value: int) -> int:
        if value == 0:
            raise serializers.ValidationError('调整积分不能为 0')
        return value


class MallCustomerSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()

    def validate_customer_id(self, value: int) -> int:
        if not Customer.objects.filter(pk=value, is_active=True).exists():
            raise serializers.ValidationError('会员不存在')
        return value


class ProductReviewSubmitSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    product_id = serializers.IntegerField()
    order_id = serializers.IntegerField(required=False, allow_null=True)
    rating = serializers.IntegerField(min_value=1, max_value=5, default=5)
    content = serializers.CharField(max_length=500)

    def validate_customer_id(self, value: int) -> int:
        if not Customer.objects.filter(pk=value, is_active=True).exists():
            raise serializers.ValidationError('会员不存在')
        return value
