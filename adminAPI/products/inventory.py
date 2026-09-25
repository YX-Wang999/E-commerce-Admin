"""Inventory change recording helpers."""

import logging
from contextvars import ContextVar

from products.models import InventoryLog, Product

logger = logging.getLogger(__name__)

_inventory_context: ContextVar[dict] = ContextVar('inventory_context', default={})


def set_inventory_context(**kwargs) -> None:
    """Set context for the next product stock save."""
    current = _inventory_context.get({}).copy()
    current.update(kwargs)
    _inventory_context.set(current)


def clear_inventory_context() -> None:
    """Clear inventory context."""
    _inventory_context.set({})


def get_inventory_context() -> dict:
    """Get current inventory context."""
    return _inventory_context.get({})


def infer_change_type(before: int, after: int) -> str:
    """Infer manual stock change type."""
    if after > before:
        return InventoryLog.TYPE_GAIN
    return InventoryLog.TYPE_LOSS


def record_inventory_change(
    product: Product,
    before_quantity: int,
    after_quantity: int,
    *,
    change_type: str | None = None,
    changed_by=None,
    order=None,
    remark: str = '',
) -> InventoryLog | None:
    """Create inventory log when stock changes."""
    if before_quantity == after_quantity:
        return None

    ctx = get_inventory_context()
    resolved_type = change_type or ctx.get('change_type') or infer_change_type(before_quantity, after_quantity)
    resolved_user = changed_by if changed_by is not None else ctx.get('changed_by')
    resolved_order = order if order is not None else ctx.get('order')
    resolved_remark = remark or ctx.get('remark', '')

    return InventoryLog.objects.create(
        product=product,
        change_type=resolved_type,
        before_quantity=before_quantity,
        after_quantity=after_quantity,
        changed_by=resolved_user,
        order=resolved_order,
        remark=resolved_remark,
    )
