"""Risk-based captcha trust assessment for login."""

from __future__ import annotations

from django.core.cache import cache

from accounts.login_guard import get_failure_count, is_locked

TRUST_HIGH = 'high'
TRUST_MEDIUM = 'medium'
TRUST_LOW = 'low'

TRUSTED_DEVICE_TTL = 60 * 60 * 24 * 30
TRUSTED_LOGIN_TTL = 60 * 60 * 24 * 7
IP_ATTEMPT_TTL = 300
SUSPICIOUS_IP_THRESHOLD = 10

TRUSTED_DEVICE_PREFIX = 'trusted_device:'
TRUSTED_LOGIN_PREFIX = 'trusted_login:'
TRUSTED_USER_DEVICE_PREFIX = 'trusted_user_device:'
IP_ATTEMPT_PREFIX = 'ip_login_attempt:'


def get_device_id(request) -> str:
    """Read client device fingerprint from header or body."""
    raw = request.headers.get('X-Device-Id') or request.data.get('device_id') or ''
    return str(raw).strip()[:64]


def _ip_attempt_key(ip: str) -> str:
    return f'{IP_ATTEMPT_PREFIX}{ip or "unknown"}'


def record_ip_login_attempt(ip: str) -> None:
    """Track login attempts per IP for suspicious-IP detection."""
    key = _ip_attempt_key(ip)
    count = int(cache.get(key, 0)) + 1
    cache.set(key, count, IP_ATTEMPT_TTL)


def is_suspicious_ip(ip: str) -> bool:
    """Whether IP has too many recent login attempts."""
    return int(cache.get(_ip_attempt_key(ip), 0)) >= SUSPICIOUS_IP_THRESHOLD


def record_trusted_session(username: str, ip: str, device_id: str) -> None:
    """Mark device/IP as trusted after successful login."""
    normalized = (username or '').strip().lower()
    if not normalized:
        return
    cache.set(f'{TRUSTED_LOGIN_PREFIX}{normalized}:{ip or "unknown"}', 1, TRUSTED_LOGIN_TTL)
    if device_id:
        cache.set(f'{TRUSTED_DEVICE_PREFIX}{device_id}:{ip or "unknown"}', 1, TRUSTED_DEVICE_TTL)
        cache.set(f'{TRUSTED_USER_DEVICE_PREFIX}{normalized}:{device_id}', 1, TRUSTED_DEVICE_TTL)


def _is_high_trust(ip: str, device_id: str, username: str = '') -> bool:
    if device_id and cache.get(f'{TRUSTED_DEVICE_PREFIX}{device_id}:{ip or "unknown"}'):
        return True
    normalized = (username or '').strip().lower()
    if normalized and cache.get(f'{TRUSTED_LOGIN_PREFIX}{normalized}:{ip or "unknown"}'):
        return True
    if normalized and device_id and cache.get(f'{TRUSTED_USER_DEVICE_PREFIX}{normalized}:{device_id}'):
        return True
    return False


def _is_low_trust(ip: str, username: str = '') -> bool:
    if is_suspicious_ip(ip):
        return True
    if username:
        if is_locked(username, ip):
            return True
        if get_failure_count(username, ip) >= 2:
            return True
    return False


def assess_login_trust(request, username: str = '') -> str:
    """Return trust level: high (no captcha), medium (post-login), low (pre-action)."""
    from audit.middleware import _get_client_ip

    ip = _get_client_ip(request) or 'unknown'
    device_id = get_device_id(request)
    username = str(username or '').strip()

    if _is_low_trust(ip, username):
        return TRUST_LOW
    if _is_high_trust(ip, device_id, username):
        return TRUST_HIGH
    return TRUST_MEDIUM


def captcha_required_for_trust(trust_level: str) -> bool:
    return trust_level in (TRUST_MEDIUM, TRUST_LOW)
