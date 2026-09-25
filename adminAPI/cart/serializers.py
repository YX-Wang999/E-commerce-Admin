"""Cart serializers."""

from rest_framework import serializers

from cart.models import Cart, CartItem
from products.serializers import ProductSimpleSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """Cart line item serializer."""

    product_detail = ProductSimpleSerializer(source='product', read_only=True)
    subtotal = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_detail', 'quantity', 'selected',
            'subtotal', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class CartSerializer(serializers.ModelSerializer):
    """Cart with nested items."""

    items = CartItemSerializer(many=True, read_only=True)
    total_quantity = serializers.IntegerField(read_only=True)
    total_price = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_quantity', 'total_price', 'updated_at']
