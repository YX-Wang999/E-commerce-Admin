"""Phone number normalization (E.164)."""

from __future__ import annotations

import re

E164_PATTERN = re.compile(r'^\+[1-9]\d{7,14}$')


def normalize_phone(value: str) -> str:
    """Normalize and validate international phone number (E.164)."""
    phone = (value or '').strip().replace(' ', '').replace('-', '')
    if phone.startswith('00'):
        phone = f'+{phone[2:]}'
    if not phone.startswith('+'):
        raise ValueError('请输入含国际区号的手机号')
    if not E164_PATTERN.match(phone):
        raise ValueError('请输入正确的国际手机号')
    return phone
