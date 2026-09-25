"""Cart API views."""

import logging

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from cart.models import Cart, CartItem
from cart.serializers import CartSerializer
from common.response import error_response, success_response
from customers.permissions import IsCustomerAuthenticated
from products.models import Product

logger = logging.getLogger(__name__)


class CartViewSet(viewsets.GenericViewSet):
    """Shopping cart operations for mall customers."""

    permission_classes = [IsCustomerAuthenticated]
    serializer_class = CartSerializer

    def get_cart(self) -> Cart:
        tenant = getattr(self.request, 'tenant', None)
        cart, _ = Cart.objects.get_or_create(
            customer=self.request.customer,
            tenant=tenant,
        )
        return cart

    def _serialize_cart(self, cart: Cart) -> Response:
        cart = Cart.objects.prefetch_related('items__product').get(pk=cart.pk)
        return success_response(data=CartSerializer(cart).data)

    def _push_cart_ws(self, cart: Cart) -> None:
        customer = getattr(self.request, 'customer', None)
        if not customer:
            return
        try:
            from tenants.notify import push_cart_update

            count = sum(item.quantity for item in cart.items.all())
            push_cart_update(customer.id, count=count)
        except Exception:
            logger.exception('Push cart WS failed for customer %s', customer.id)

    @action(detail=False, methods=['get'], url_path='my_cart')
    def my_cart(self, request: Request) -> Response:
        return self._serialize_cart(self.get_cart())

    @action(detail=False, methods=['post'], url_path='add')
    def add_item(self, request: Request) -> Response:
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1) or 1)

        if not product_id:
            return error_response('商品ID不能为空')
        if quantity <= 0:
            return error_response('数量必须大于 0')

        try:
            product = Product.objects.get(pk=product_id, is_active=True)
        except Product.DoesNotExist:
            return error_response('商品不存在')

        if product.status != Product.STATUS_ON_SALE:
            return error_response('商品未上架')

        cart = self.get_cart()
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity, 'selected': True},
        )
        if not created:
            item.quantity += quantity
            if item.quantity > product.stock:
                return error_response('库存不足')
            item.save(update_fields=['quantity', 'updated_at'])
        elif item.quantity > product.stock:
            item.delete()
            return error_response('库存不足')

        self._push_cart_ws(cart)
        return self._serialize_cart(cart)

    @action(detail=False, methods=['post'], url_path='merge')
    def merge_items(self, request: Request) -> Response:
        """Merge guest local cart items into the logged-in customer cart."""
        raw_items = request.data.get('items') or []
        if not isinstance(raw_items, list):
            return error_response('参数格式不正确')

        cart = self.get_cart()
        merged_count = 0

        for entry in raw_items:
            product_id = entry.get('product_id')
            try:
                quantity = int(entry.get('quantity', 1) or 1)
            except (TypeError, ValueError):
                continue
            selected = bool(entry.get('selected', True))

            if not product_id or quantity <= 0:
                continue

            try:
                product = Product.objects.get(pk=product_id, is_active=True)
            except Product.DoesNotExist:
                continue

            if product.status != Product.STATUS_ON_SALE:
                continue

            item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity, 'selected': selected},
            )
            if not created:
                item.quantity += quantity
                if item.quantity > product.stock:
                    item.quantity = product.stock
                item.selected = selected or item.selected
                item.save(update_fields=['quantity', 'selected', 'updated_at'])
            elif item.quantity > product.stock:
                item.quantity = product.stock
                item.save(update_fields=['quantity', 'updated_at'])
            merged_count += 1

        self._push_cart_ws(cart)
        return success_response(
            data={
                **CartSerializer(
                    Cart.objects.prefetch_related('items__product').get(pk=cart.pk),
                ).data,
                'merged_count': merged_count,
            },
            message='购物车已同步',
        )

    @action(detail=False, methods=['post'], url_path='update')
    def update_item(self, request: Request) -> Response:
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity')

        if not item_id or quantity is None:
            return error_response('参数不完整')

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return error_response('数量格式不正确')

        item = get_object_or_404(CartItem, id=item_id, cart__customer=request.customer)
        if quantity <= 0:
            cart = item.cart
            item.delete()
            self._push_cart_ws(cart)
            return self._serialize_cart(cart)
        if quantity > item.product.stock:
            return error_response('库存不足')
        item.quantity = quantity
        item.save(update_fields=['quantity', 'updated_at'])
        self._push_cart_ws(item.cart)
        return self._serialize_cart(item.cart)

    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle_select(self, request: Request) -> Response:
        item_id = request.data.get('item_id')
        selected = request.data.get('selected', True)

        if not item_id:
            return error_response('参数不完整')

        item = get_object_or_404(CartItem, id=item_id, cart__customer=request.customer)
        item.selected = bool(selected)
        item.save(update_fields=['selected', 'updated_at'])
        return self._serialize_cart(item.cart)

    @action(detail=False, methods=['post'], url_path='toggle-all')
    def toggle_all(self, request: Request) -> Response:
        selected = bool(request.data.get('selected', True))
        cart = self.get_cart()
        cart.items.update(selected=selected)
        return self._serialize_cart(cart)

    @action(detail=False, methods=['delete'], url_path='clear')
    def clear(self, request: Request) -> Response:
        cart = self.get_cart()
        cart.items.all().delete()
        self._push_cart_ws(cart)
        return self._serialize_cart(cart)

    @action(detail=False, methods=['delete'], url_path='remove')
    def remove_item(self, request: Request) -> Response:
        item_id = request.data.get('item_id')
        if not item_id:
            return error_response('商品ID不能为空')
        item = get_object_or_404(CartItem, id=item_id, cart__customer=request.customer)
        cart = item.cart
        item.delete()
        self._push_cart_ws(cart)
        return self._serialize_cart(cart)
