"""Order queryset filters by user role."""

from django.contrib.auth import get_user_model

from orders.models import Order

User = get_user_model()

ELEVATED_ROLES = {'super_admin', 'ops_manager'}


def resolve_role_codes(user) -> set[str]:
    """Get active role codes for user."""
    if getattr(user, 'is_superuser', False):
        return {'super_admin'}
    roles = getattr(user, 'roles', None)
    if roles is None:
        return set()
    return set(roles.filter(is_active=True).values_list('code', flat=True))


def apply_order_role_filter(queryset, user, customer=None):
    """Filter orders by role-based data access rules."""
    if customer is not None:
        return queryset.filter(customer=customer)

    roles = resolve_role_codes(user)

    if user.is_superuser or roles & ELEVATED_ROLES:
        return queryset

    if 'ops_staff' in roles:
        return queryset.filter(assigned_to=user)

    if 'warehouse_manager' in roles:
        return queryset.filter(status__in=[Order.STATUS_PAID, Order.STATUS_SHIPPED])

    if roles == {'cs_staff'}:
        return queryset.filter(status__in=[Order.STATUS_COMPLETED, Order.STATUS_CANCELLED])

    if 'data_analyst' in roles:
        return queryset

    return queryset.none()
