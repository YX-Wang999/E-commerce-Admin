"""Tenant profile field sensitivity for change review."""

from __future__ import annotations

# Direct update — no platform review required
LOW_SENSITIVITY_FIELDS = frozenset({'address', 'logo', 'config', 'description'})

# Requires platform review — medium
MEDIUM_SENSITIVITY_FIELDS = frozenset({'contact_name', 'contact_email'})

# Requires platform review — high
HIGH_SENSITIVITY_FIELDS = frozenset({'name', 'contact_phone', 'legal_person', 'business_license'})

REVIEW_REQUIRED_FIELDS = MEDIUM_SENSITIVITY_FIELDS | HIGH_SENSITIVITY_FIELDS

FIELD_LABELS: dict[str, str] = {
    'name': '店铺名称',
    'contact_phone': '联系电话',
    'contact_email': '联系邮箱',
    'contact_name': '联系人',
    'legal_person': '法人姓名',
    'business_license': '营业执照',
    'address': '店铺地址',
    'description': '店铺描述',
    'logo': 'Logo',
    'config': '店铺配置',
}

PENDING_FIELD_MAP: dict[str, str] = {
    'name': 'pending_name',
    'contact_phone': 'pending_contact_phone',
    'contact_email': 'pending_contact_email',
    'contact_name': 'pending_contact_name',
    'legal_person': 'pending_legal_person',
    'business_license': 'pending_business_license',
}

OFFICIAL_FIELD_MAP: dict[str, str] = {value: key for key, value in PENDING_FIELD_MAP.items()}
