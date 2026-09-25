"""Product model signals for inventory logging."""

import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from products.inventory import clear_inventory_context, get_inventory_context, record_inventory_change
from products.models import InventoryLog, Product

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Product)
def capture_product_stock(sender, instance: Product, **kwargs) -> None:
    """Store previous stock before save."""
    if instance.pk:
        instance._old_stock = Product.objects.filter(pk=instance.pk).values_list('stock', flat=True).first()
    else:
        instance._old_stock = None


@receiver(post_save, sender=Product)
def log_product_stock_change(sender, instance: Product, created: bool, **kwargs) -> None:
    """Record inventory log when product stock changes."""
    ctx = get_inventory_context()
    if ctx.get('skip_log'):
        clear_inventory_context()
        return

    try:
        if created:
            if instance.stock > 0:
                record_inventory_change(
                    instance,
                    0,
                    instance.stock,
                    change_type=ctx.get('change_type', InventoryLog.TYPE_STOCK_IN),
                    remark=ctx.get('remark', '商品创建初始库存'),
                )
            return

        old_stock = getattr(instance, '_old_stock', None)
        if old_stock is None or old_stock == instance.stock:
            return

        record_inventory_change(instance, old_stock, instance.stock)
    finally:
        clear_inventory_context()
