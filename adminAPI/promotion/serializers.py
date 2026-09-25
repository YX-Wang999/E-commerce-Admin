"""Promotion serializers."""

from rest_framework import serializers

from products.models import Category, Product
from promotion.models import Coupon, GroupBuyActivity, GroupOrder, SeckillActivity, SuperDiscount, UserCoupon


class PromotionProductSerializer(serializers.ModelSerializer):
    """Minimal product info for promotion."""

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'stock', 'status']


class SeckillActivitySerializer(serializers.ModelSerializer):
    """Seckill activity read/write serializer."""

    product_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Product.objects.filter(is_active=True),
        source='products',
        write_only=True,
    )
    products = PromotionProductSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.nickname', read_only=True, default='')
    approved_by_name = serializers.CharField(source='approved_by.nickname', read_only=True, default='')
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SeckillActivity
        fields = [
            'id', 'name', 'product_ids', 'products', 'seckill_price', 'seckill_stock',
            'per_user_limit', 'start_time', 'end_time', 'warmup_time', 'status', 'status_label',
            'reject_reason', 'approved_by', 'approved_by_name', 'approved_at',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'status', 'reject_reason', 'approved_by', 'approved_at',
            'created_by', 'created_at', 'updated_at',
        ]

    def validate(self, attrs: dict) -> dict:
        """Validate time range and product count."""
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        warmup_time = attrs.get('warmup_time')
        products = attrs.get('products')

        if self.instance:
            start_time = start_time if start_time is not None else self.instance.start_time
            end_time = end_time if end_time is not None else self.instance.end_time
            warmup_time = warmup_time if 'warmup_time' in attrs else self.instance.warmup_time

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({'end_time': '结束时间必须晚于开始时间'})
        if warmup_time and start_time and warmup_time >= start_time:
            raise serializers.ValidationError({'warmup_time': '预热时间必须早于开始时间'})
        if products is not None and not products:
            raise serializers.ValidationError({'product_ids': '请至少选择一个商品'})
        if products is not None and len(products) > 3:
            raise serializers.ValidationError({'product_ids': '参与商品最多 3 个'})
        return attrs


class GroupBuyActivitySerializer(serializers.ModelSerializer):
    """Group buy activity serializer."""

    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True),
        source='product',
        write_only=True,
    )
    product = PromotionProductSerializer(read_only=True)
    created_by_name = serializers.CharField(source='created_by.nickname', read_only=True, default='')
    approved_by_name = serializers.CharField(source='approved_by.nickname', read_only=True, default='')
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = GroupBuyActivity
        fields = [
            'id', 'name', 'product_id', 'product', 'group_price', 'group_size', 'stock',
            'per_user_limit', 'group_valid_hours', 'auto_group', 'start_time', 'end_time',
            'status', 'status_label', 'reject_reason', 'approved_by', 'approved_by_name',
            'approved_at', 'created_by', 'created_by_name', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'status', 'reject_reason', 'approved_by', 'approved_at',
            'created_by', 'created_at', 'updated_at',
        ]

    def validate(self, attrs: dict) -> dict:
        """Validate group buy fields."""
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        group_size = attrs.get('group_size')

        if self.instance:
            start_time = start_time if start_time is not None else self.instance.start_time
            end_time = end_time if end_time is not None else self.instance.end_time
            group_size = group_size if group_size is not None else self.instance.group_size

        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({'end_time': '结束时间必须晚于开始时间'})
        if group_size is not None and group_size < 2:
            raise serializers.ValidationError({'group_size': '成团人数至少为 2 人'})
        return attrs


class GroupOrderSerializer(serializers.ModelSerializer):
    """Group order read serializer."""

    activity_name = serializers.CharField(source='activity.name', read_only=True)
    order_no = serializers.CharField(source='order.order_no', read_only=True)
    captain_name = serializers.CharField(source='captain.nickname', read_only=True, default='')
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = GroupOrder
        fields = [
            'id', 'activity', 'activity_name', 'order', 'order_no', 'captain', 'captain_name',
            'status', 'status_label', 'expired_at', 'created_at',
        ]


class CouponSerializer(serializers.ModelSerializer):
    """Coupon read/write serializer."""

    product_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Product.objects.filter(is_active=True),
        source='applicable_products',
        write_only=True,
        required=False,
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        source='applicable_category',
        write_only=True,
        required=False,
        allow_null=True,
    )
    applicable_products = PromotionProductSerializer(many=True, read_only=True)
    applicable_category_name = serializers.CharField(
        source='applicable_category.name',
        read_only=True,
        default='',
    )
    created_by_name = serializers.CharField(source='created_by.nickname', read_only=True, default='')
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    received_count = serializers.SerializerMethodField()
    used_count = serializers.SerializerMethodField()

    class Meta:
        model = Coupon
        fields = [
            'id', 'name', 'coupon_type', 'discount_amount', 'discount_rate', 'max_discount',
            'min_amount', 'total_quantity', 'per_user_limit', 'applicable_scope',
            'category_id', 'applicable_category', 'applicable_category_name',
            'product_ids', 'applicable_products', 'valid_type', 'valid_start', 'valid_end',
            'valid_days', 'status', 'status_label', 'created_by', 'created_by_name',
            'received_count', 'used_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'status', 'created_by', 'created_at', 'updated_at']

    def get_received_count(self, obj: Coupon) -> int:
        """Return total received count."""
        return obj.user_coupons.count()

    def get_used_count(self, obj: Coupon) -> int:
        """Return used count."""
        return obj.user_coupons.filter(status=UserCoupon.STATUS_USED).count()

    def validate(self, attrs: dict) -> dict:
        """Validate coupon fields by type."""
        coupon_type = attrs.get('coupon_type')
        if self.instance and coupon_type is None:
            coupon_type = self.instance.coupon_type

        if coupon_type == Coupon.TYPE_FIXED and attrs.get('discount_amount') is None:
            if not self.instance or 'discount_amount' in attrs:
                if attrs.get('discount_amount') is None and (not self.instance or not self.instance.discount_amount):
                    raise serializers.ValidationError({'discount_amount': '满减券需填写面额'})

        if coupon_type == Coupon.TYPE_DISCOUNT:
            rate = attrs.get('discount_rate')
            if rate is None and self.instance:
                rate = self.instance.discount_rate
            if rate is None:
                raise serializers.ValidationError({'discount_rate': '折扣券需填写折扣率'})

        scope = attrs.get('applicable_scope')
        if self.instance and scope is None:
            scope = self.instance.applicable_scope

        if scope == Coupon.SCOPE_CATEGORY:
            category = attrs.get('applicable_category')
            if category is None and self.instance:
                category = self.instance.applicable_category
            if category is None:
                raise serializers.ValidationError({'category_id': '请选择适用分类'})

        if scope == Coupon.SCOPE_PRODUCT:
            products = attrs.get('applicable_products')
            if products is None and self.instance:
                products = list(self.instance.applicable_products.all())
            if not products:
                raise serializers.ValidationError({'product_ids': '请选择适用商品'})

        valid_type = attrs.get('valid_type')
        if self.instance and valid_type is None:
            valid_type = self.instance.valid_type

        if valid_type == Coupon.VALID_FIXED:
            valid_start = attrs.get('valid_start')
            valid_end = attrs.get('valid_end')
            if self.instance:
                valid_start = valid_start if valid_start is not None else self.instance.valid_start
                valid_end = valid_end if valid_end is not None else self.instance.valid_end
            if not valid_start or not valid_end:
                raise serializers.ValidationError({'valid_start': '固定有效期需填写开始和结束时间'})
            if valid_start >= valid_end:
                raise serializers.ValidationError({'valid_end': '结束时间必须晚于开始时间'})

        if valid_type == Coupon.VALID_AFTER_RECEIVE:
            valid_days = attrs.get('valid_days')
            if valid_days is None and self.instance:
                valid_days = self.instance.valid_days
            if not valid_days:
                raise serializers.ValidationError({'valid_days': '请填写领取后有效天数'})

        return attrs


class UserCouponSerializer(serializers.ModelSerializer):
    """User coupon record serializer."""

    coupon_name = serializers.CharField(source='coupon.name', read_only=True)
    user_name = serializers.CharField(source='user.nickname', read_only=True, default='')
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = UserCoupon
        fields = [
            'id', 'coupon', 'coupon_name', 'user', 'user_name', 'code', 'status', 'status_label',
            'received_at', 'used_at', 'expired_at', 'order',
        ]


class SuperDiscountSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.nickname', read_only=True, default='')

    class Meta:
        model = SuperDiscount
        fields = [
            'id', 'title', 'promo_text', 'amount', 'button_text', 'link_url',
            'is_active', 'start_time', 'end_time',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_by_name', 'created_at', 'updated_at']
