"""Mall customer login helpers."""

from __future__ import annotations

from customers.models import Customer
from customers.phone_utils import normalize_phone


def resolve_customer_by_account(account: str) -> Customer | None:
    """Find customer by phone, nickname, email, or name."""
    value = (account or '').strip()
    if not value:
        return None

    customer = _lookup_by_phone(value)
    if customer:
        return customer

    customer = Customer.objects.filter(nickname__iexact=value).first()
    if customer:
        return customer

    if '@' in value:
        customer = Customer.objects.filter(email__iexact=value).first()
        if customer:
            return customer

    return Customer.objects.filter(name__iexact=value).first()


def _lookup_by_phone(value: str) -> Customer | None:
    raw = value.replace(' ', '').replace('-', '')
    if raw.startswith('00'):
        raw = f'+{raw[2:]}'

    candidates: list[str] = []
    if raw.startswith('+'):
        candidates.append(raw)
    elif raw.isdigit():
        if len(raw) == 11:
            candidates.append(f'+86{raw}')
        elif len(raw) >= 8:
            candidates.append(f'+{raw}')

    for phone_raw in candidates:
        try:
            phone = normalize_phone(phone_raw)
        except ValueError:
            continue
        customer = Customer.objects.filter(phone=phone).first()
        if customer:
            return customer
    return None
