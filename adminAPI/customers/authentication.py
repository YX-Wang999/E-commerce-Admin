"""Customer JWT authentication for mall API."""

from rest_framework import authentication, exceptions
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from customers.models import Customer


class CustomerAuthUser:
    """Minimal principal so DRF IsAuthenticated works for mall users."""

    is_authenticated = True
    is_anonymous = False

    def __init__(self, customer: Customer):
        self.customer = customer
        self.id = customer.id
        self.pk = customer.id


class CustomerJWTAuthentication(authentication.BaseAuthentication):
    """Authenticate mall requests via customer JWT."""

    www_authenticate_header = 'Bearer'

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode('utf-8')
        if not header.startswith('Bearer '):
            return None
        raw_token = header[7:].strip()
        if not raw_token:
            return None
        try:
            validated = AccessToken(raw_token)
        except (InvalidToken, TokenError) as exc:
            raise exceptions.AuthenticationFailed('登录已失效，请重新登录') from exc

        customer_id = validated.get('customer_id')
        if not customer_id:
            return None

        try:
            customer = Customer.objects.get(pk=customer_id, is_active=True)
        except Customer.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed('账号不存在或已被禁用') from exc

        request.customer = customer
        return CustomerAuthUser(customer), validated
