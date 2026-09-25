"""Order serializers."""

from rest_framework import serializers

from logistics.serializers import LogisticsSerializer
from orders.models import CancelLog, Order, OrderItem, Refund


class OrderItemSerializer(serializers.ModelSerializer):
    """Order item serializer."""

    product_name = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_product_name(self, obj: OrderItem) -> str:
        return obj.product_name or obj.product.name


class CustomerOrderItemSerializer(serializers.Serializer):
    """Checkout line item from cart."""

    cart_item_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class CustomerCheckoutSerializer(serializers.Serializer):
    """Mall checkout payload."""

    address_id = serializers.IntegerField()
    items = CustomerOrderItemSerializer(many=True)
    remark = serializers.CharField(required=False, allow_blank=True, default='')
    coupon_id = serializers.IntegerField(required=False, allow_null=True)
    use_points = serializers.BooleanField(required=False, default=False)
    points_amount = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    use_seller_points = serializers.BooleanField(required=False, default=False)
    seller_points_amount = serializers.IntegerField(required=False, allow_null=True, min_value=0)


class CustomerOrderResultSerializer(serializers.ModelSerializer):
    """Minimal order response after checkout."""

    class Meta:
        model = Order
        fields = ['id', 'order_no', 'total_amount', 'original_amount', 'coupon_discount', 'points_discount', 'points_used', 'seller_points_discount', 'seller_points_used', 'status', 'paid_at', 'expires_at', 'created_at']


class CancelLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CancelLog
        fields = ['id', 'action', 'reason', 'remark', 'operator_type', 'operator_id', 'created_at']


class OrderCancelApplySerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255)
    detail = serializers.CharField(required=False, allow_blank=True, default='')


class OrderCancelReviewSerializer(serializers.Serializer):
    approve = serializers.BooleanField()
    remark = serializers.CharField(required=False, allow_blank=True, default='')


class OrderCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255)
    detail = serializers.CharField(required=False, allow_blank=True, default='')


class RefundSerializer(serializers.ModelSerializer):
    """Refund serializer."""

    order_no = serializers.CharField(source='order.order_no', read_only=True)

    class Meta:
        model = Refund
        fields = [
            'id', 'order', 'order_no', 'reason', 'amount', 'status',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrderSerializer(serializers.ModelSerializer):
    """Order read serializer."""

    customer_name = serializers.CharField(source='customer.name', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    logistics = LogisticsSerializer(read_only=True)
    cancel_logs = CancelLogSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_no', 'customer', 'customer_name', 'tenant', 'tenant_name', 'total_amount',
            'status', 'address', 'logistics_no', 'logistics', 'remark', 'paid_at', 'expires_at', 'items',
            'cancel_status', 'cancel_type', 'cancel_reason', 'cancel_detail', 'cancel_review_remark',
            'cancelled_at', 'shipped_at', 'completed_at', 'receipt_type', 'cancel_logs', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'order_no', 'created_at', 'updated_at']


class OrderItemCreateSerializer(serializers.Serializer):
    """Order item create payload."""

    product = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)


class OrderCreateSerializer(serializers.ModelSerializer):
    """Order create serializer."""

    items = OrderItemCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = ['customer', 'address', 'remark', 'items']
