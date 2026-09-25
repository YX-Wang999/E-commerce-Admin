"""Supported express companies (Kuaidi100 codes)."""

import re

EXPRESS_COMPANIES = [
    {'code': 'shunfeng', 'name': '顺丰速运'},
    {'code': 'yuantong', 'name': '圆通速递'},
    {'code': 'zhongtong', 'name': '中通快递'},
    {'code': 'shentong', 'name': '申通快递'},
    {'code': 'yunda', 'name': '韵达快递'},
    {'code': 'jtexpress', 'name': '极兔速递'},
    {'code': 'jd', 'name': '京东物流'},
    {'code': 'ems', 'name': 'EMS'},
    {'code': 'debangkuaidi', 'name': '德邦物流'},
    {'code': 'huitongkuaidi', 'name': '百世快递'},
]

_CODE_TO_NAME = {item['code']: item['name'] for item in EXPRESS_COMPANIES}
_CODE_ALIASES = {
    'sf': 'shunfeng',
    'yto': 'yuantong',
    'zto': 'zhongtong',
    'sto': 'shentong',
    'jt': 'jtexpress',
    'debang': 'debangkuaidi',
}
_TRACKING_PATTERN = re.compile(r'^[A-Za-z0-9-]{6,32}$')


def normalize_express_code(code: str) -> str:
    value = (code or '').strip().lower()
    return _CODE_ALIASES.get(value, value)


def get_company_name(code: str) -> str:
    return _CODE_TO_NAME.get(normalize_express_code(code), code)


def is_valid_express_code(code: str) -> bool:
    return normalize_express_code(code) in _CODE_TO_NAME


def validate_tracking_number(number: str) -> str | None:
    """Return error message if invalid, else None."""
    value = (number or '').strip()
    if not value:
        return '请填写物流单号'
    if len(value) > 100:
        return '物流单号过长'
    if not _TRACKING_PATTERN.match(value):
        return '物流单号格式不正确（6-32位字母数字）'
    return None
