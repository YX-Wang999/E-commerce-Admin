"""Tenant / shop name validation rules."""

from __future__ import annotations

import json
import re

TENANT_NAME_PATTERN = re.compile(r'^[\u4e00-\u9fa5a-zA-Z0-9·\- ]{2,50}$')
SENSITIVE_WORDS_KEY = 'tenant_name_sensitive_words'


def name_effective_length(name: str) -> int:
    """Chinese counts as 2, others as 1 (min effective length = 4)."""
    total = 0
    for char in name:
        if '\u4e00' <= char <= '\u9fa5':
            total += 2
        else:
            total += 1
    return total


def is_all_digits_or_symbols(name: str) -> bool:
    stripped = re.sub(r'[\s·\-]', '', name)
    if not stripped:
        return True
    if stripped.isdigit():
        return True
    return not re.search(r'[\u4e00-\u9fa5a-zA-Z]', stripped)


def get_sensitive_words() -> list[str]:
    from system.models import SystemSetting

    row = SystemSetting.objects.filter(key=SENSITIVE_WORDS_KEY).first()
    if not row or not row.value:
        return []
    raw = str(row.value).strip()
    if raw.startswith('['):
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [str(item).strip() for item in data if str(item).strip()]
        except json.JSONDecodeError:
            pass
    return [part.strip() for part in re.split(r'[,，\n;；|]', raw) if part.strip()]


def find_sensitive_word(name: str) -> str | None:
    lowered = name.lower()
    for word in get_sensitive_words():
        if word.lower() in lowered:
            return word
    return None


def validate_tenant_name(name: str) -> str | None:
    """Return error message, or None when valid."""
    value = (name or '').strip()
    if not value:
        return '商户名称不能为空'
    if not TENANT_NAME_PATTERN.match(value):
        return '名称仅允许中文、英文、数字、点、横杠和空格，长度 2-50 个字符'
    if name_effective_length(value) < 4:
        return '名称长度至少 2 个汉字或 4 个字符'
    if is_all_digits_or_symbols(value):
        return '商户名称不能全是数字或特殊符号'
    sensitive = find_sensitive_word(value)
    if sensitive:
        return f'商户名称包含敏感词「{sensitive}」'
    return None
