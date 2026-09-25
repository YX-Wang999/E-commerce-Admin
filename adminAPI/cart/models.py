"""Shopping cart models."""

from decimal import Decimal

from django.db import models

from common.tenant import TenantAwareManager


class Cart(models.Model):
    """Customer shopping cart."""

    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='carts',
        verbose_name='商城用户',
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='carts',
        null=True,
        blank=True,
        verbose_name='商家',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    objects = TenantAwareManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'cart_cart'
        verbose_name = '购物车'
        verbose_name_plural = verbose_name
        unique_together = [('customer', 'tenant')]

    def __str__(self) -> str:
        return f'Cart({self.customer_id})'

    @property
    def total_quantity(self) -> int:
        return sum(item.quantity for item in self.items.filter(selected=True))

    @property
    def total_price(self) -> Decimal:
        total = Decimal('0')
        for item in self.items.filter(selected=True).select_related('product'):
            total += item.subtotal
        return total


class CartItem(models.Model):
    """Line item in a shopping cart."""

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='购物车',
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        verbose_name='商品',
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='数量')
    selected = models.BooleanField(default=True, verbose_name='是否选中')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'cart_cart_item'
        verbose_name = '购物车商品'
        verbose_name_plural = verbose_name
        unique_together = ['cart', 'product']

    def __str__(self) -> str:
        return f'CartItem({self.cart_id}, {self.product_id})'

    @property
    def subtotal(self) -> Decimal:
        return Decimal(str(self.product.price)) * self.quantity
