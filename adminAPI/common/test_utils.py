"""Shared helpers for API tests."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from customers.models import Customer
from customers.tokens import CustomerRefreshToken
from rbac.models import Role

User = get_user_model()


def create_staff_user(
    username: str,
    password: str = 'TestPass123!',
    *,
    role_code: str | None = None,
    is_first_login: bool = False,
) -> User:
    user = User.objects.create_user(username=username, password=password)
    user.is_first_login = is_first_login
    user.save(update_fields=['is_first_login'])
    if role_code:
        role, _ = Role.objects.get_or_create(
            code=role_code,
            defaults={'name': role_code, 'description': role_code, 'is_active': True},
        )
        user.roles.add(role)
    return user


def staff_access_token(user: User) -> str:
    return str(RefreshToken.for_user(user).access_token)


def auth_staff(client: APIClient, user: User) -> APIClient:
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {staff_access_token(user)}')
    return client


def create_customer(phone: str = '+8613800009999', password: str = 'TestPass123!') -> Customer:
    customer = Customer(phone=phone, nickname='测试用户', name='测试用户', is_active=True)
    customer.set_password(password)
    customer.save()
    return customer


def customer_access_token(customer: Customer) -> str:
    return str(CustomerRefreshToken.for_customer(customer).access_token)


def auth_customer(client: APIClient, customer: Customer) -> APIClient:
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {customer_access_token(customer)}')
    return client
