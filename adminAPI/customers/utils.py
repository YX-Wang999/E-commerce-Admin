"""Request helpers for mall customers."""

from customers.models import Customer


def get_request_customer(request) -> Customer | None:
    return getattr(request, 'customer', None)
