"""JWT tokens for mall customers."""

from datetime import timedelta

from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


class CustomerAccessToken(AccessToken):
    """Access token carrying customer_id (token_type stays 'access' per simplejwt)."""

    lifetime = getattr(
        settings,
        'CUSTOMER_JWT_ACCESS_LIFETIME',
        timedelta(days=7),
    )

    @classmethod
    def for_customer(cls, customer) -> 'CustomerAccessToken':
        token = cls()
        token['customer_id'] = customer.id
        return token


class CustomerRefreshToken(RefreshToken):
    """Refresh token carrying customer_id claim."""

    access_token_class = CustomerAccessToken
    lifetime = getattr(
        settings,
        'CUSTOMER_JWT_REFRESH_LIFETIME',
        timedelta(days=90),
    )

    @classmethod
    def for_customer(cls, customer) -> 'CustomerRefreshToken':
        token = cls()
        token['customer_id'] = customer.id
        token['token_type'] = 'customer'
        return token

    @property
    def access_token(self) -> CustomerAccessToken:
        access = super().access_token
        access['customer_id'] = self.get('customer_id')
        return access
