"""WebSocket JWT authentication middleware."""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from customers.models import Customer

User = get_user_model()


@database_sync_to_async
def _get_user(user_id: int):
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


@database_sync_to_async
def _get_customer(customer_id: int):
    try:
        return Customer.objects.get(pk=customer_id, is_active=True)
    except Customer.DoesNotExist:
        return None


class JWTAuthMiddleware(BaseMiddleware):
    """Authenticate WebSocket via ?token= JWT (staff User or mall Customer)."""

    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        scope['user'] = AnonymousUser()
        scope['customer'] = None
        user, customer = await self._authenticate(scope)
        scope['user'] = user
        scope['customer'] = customer
        return await super().__call__(scope, receive, send)

    async def _authenticate(self, scope):
        query_string = scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        token = params.get('token', [None])[0]
        if not token:
            return AnonymousUser(), None
        try:
            validated = AccessToken(token)
        except (InvalidToken, TokenError):
            return AnonymousUser(), None

        customer_id = validated.get('customer_id')
        if customer_id:
            customer = await _get_customer(int(customer_id))
            return AnonymousUser(), customer

        user_id = validated.get('user_id')
        if not user_id:
            return AnonymousUser(), None
        user = await _get_user(int(user_id))
        return user, None


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
