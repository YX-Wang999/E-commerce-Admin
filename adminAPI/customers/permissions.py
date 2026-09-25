"""Customer API permissions."""

from rest_framework.permissions import BasePermission

from customers.exceptions import CustomerLoginRequired


class IsCustomerAuthenticated(BasePermission):
    """Allow only authenticated mall customers."""

    message = '请先登录'

    def has_permission(self, request, view) -> bool:
        if getattr(request, 'customer', None) is not None:
            return True
        raise CustomerLoginRequired()
