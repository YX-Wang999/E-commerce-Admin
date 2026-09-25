"""Role display name configuration stored in SystemSetting."""

from __future__ import annotations

import json
from typing import Any

from accounts.rbac_seed import ROLE_MATRIX
from rbac.models import Role
from system.models import SystemSetting

ROLE_DISPLAY_NAMES_KEY = 'role_display_names'
SUPPORTED_LOCALES = ('zh-CN', 'en-US', 'ja-JP')

# Built-in defaults (used when custom name for a locale is empty)
DEFAULT_LOCALE_NAMES: dict[str, dict[str, str]] = {
    'super_admin': {
        'zh-CN': '超级管理员',
        'en-US': 'Super Admin',
        'ja-JP': 'スーパー管理者',
    },
    'ops_director': {
        'zh-CN': '运营总监',
        'en-US': 'Operations Director',
        'ja-JP': '運営ディレクター',
    },
    'ops_manager': {
        'zh-CN': '运营主管',
        'en-US': 'Operations Manager',
        'ja-JP': '運営マネージャー',
    },
    'ops_staff': {
        'zh-CN': '运营专员',
        'en-US': 'Operations Specialist',
        'ja-JP': '運営スタッフ',
    },
    'cs_staff': {
        'zh-CN': '客服专员',
        'en-US': 'Customer Service Agent',
        'ja-JP': 'カスタマーサポート',
    },
    'warehouse_manager': {
        'zh-CN': '仓库管理员',
        'en-US': 'Warehouse Manager',
        'ja-JP': '倉庫管理者',
    },
    'data_analyst': {
        'zh-CN': '数据分析师',
        'en-US': 'Data Analyst',
        'ja-JP': 'データアナリスト',
    },
    'dept_manager': {
        'zh-CN': '部门经理',
        'en-US': 'Department Manager',
        'ja-JP': '部門マネージャー',
    },
    'employee': {
        'zh-CN': '普通员工',
        'en-US': 'Employee',
        'ja-JP': '一般社員',
    },
    'customer': {
        'zh-CN': '商城用户',
        'en-US': 'Mall Customer',
        'ja-JP': 'モールユーザー',
    },
}


def _role_codes() -> list[str]:
    db_codes = list(Role.objects.order_by('id').values_list('code', flat=True))
    if db_codes:
        return db_codes
    return list(ROLE_MATRIX.keys())


def build_default_names() -> dict[str, dict[str, str]]:
    """Merge ROLE_MATRIX zh names with built-in locale defaults."""
    result: dict[str, dict[str, str]] = {}
    for code in _role_codes():
        matrix_name = ROLE_MATRIX.get(code, {}).get('name', code)
        locale_map = dict(DEFAULT_LOCALE_NAMES.get(code, {}))
        locale_map.setdefault('zh-CN', matrix_name)
        for locale in SUPPORTED_LOCALES:
            locale_map.setdefault(locale, matrix_name)
        result[code] = locale_map
    return result


def _load_custom_raw() -> dict[str, dict[str, str]]:
    row = SystemSetting.objects.filter(key=ROLE_DISPLAY_NAMES_KEY).first()
    if not row or not row.value:
        return {}
    try:
        data = json.loads(row.value)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    cleaned: dict[str, dict[str, str]] = {}
    for code, names in data.items():
        if not isinstance(names, dict):
            continue
        cleaned[code] = {
            locale: str(names.get(locale, '')).strip()
            for locale in SUPPORTED_LOCALES
        }
    return cleaned


def get_merged_names() -> dict[str, dict[str, str]]:
    """Default names merged with non-empty custom overrides."""
    defaults = build_default_names()
    custom = _load_custom_raw()
    merged: dict[str, dict[str, str]] = {}
    for code in _role_codes():
        base = dict(defaults.get(code, {}))
        overrides = custom.get(code, {})
        for locale in SUPPORTED_LOCALES:
            custom_value = overrides.get(locale, '')
            if custom_value:
                base[locale] = custom_value
        merged[code] = base
    return merged


def resolve_role_name(code: str, locale: str = 'zh-CN', fallback: str = '') -> str:
    """Resolve display name for a role code and locale."""
    if not code:
        return fallback or '-'
    merged = get_merged_names()
    names = merged.get(code, {})
    if locale in names and names[locale]:
        return names[locale]
    if 'zh-CN' in names and names['zh-CN']:
        return names['zh-CN']
    return fallback or code


def get_role_display_payload() -> dict[str, Any]:
    """Payload for GET /role-display-names/."""
    defaults = build_default_names()
    custom = _load_custom_raw()
    merged = get_merged_names()
    items = []
    for code in _role_codes():
        role = Role.objects.filter(code=code).first()
        items.append({
            'code': code,
            'default_name': role.name if role else defaults.get(code, {}).get('zh-CN', code),
            'default_names': defaults.get(code, {}),
            'custom_names': custom.get(code, {loc: '' for loc in SUPPORTED_LOCALES}),
            'display_names': merged.get(code, {}),
        })
    return {
        'locales': list(SUPPORTED_LOCALES),
        'items': items,
        'merged': merged,
    }


def save_role_display_names(payload: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Persist custom names; empty string clears override for that locale."""
    if not isinstance(payload, dict):
        raise ValueError('请求体必须是 JSON 对象')

    known_codes = set(_role_codes())
    cleaned: dict[str, dict[str, str]] = {}
    for code, names in payload.items():
        if code not in known_codes:
            continue
        if not isinstance(names, dict):
            continue
        cleaned[code] = {
            locale: str(names.get(locale, '')).strip()
            for locale in SUPPORTED_LOCALES
        }

    SystemSetting.objects.update_or_create(
        key=ROLE_DISPLAY_NAMES_KEY,
        defaults={
            'value': json.dumps(cleaned, ensure_ascii=False),
            'value_type': SystemSetting.VALUE_TYPE_STRING,
            'description': '角色多语言显示名称（JSON）',
        },
    )
    return get_merged_names()


def seed_role_display_names_setting() -> None:
    """Ensure setting row exists (custom JSON may remain empty)."""
    SystemSetting.objects.get_or_create(
        key=ROLE_DISPLAY_NAMES_KEY,
        defaults={
            'value': '{}',
            'value_type': SystemSetting.VALUE_TYPE_STRING,
            'description': '角色多语言显示名称（JSON）',
        },
    )
