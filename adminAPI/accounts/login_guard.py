"""Login failure tracking and temporary lock."""

from __future__ import annotations

from django.core.cache import cache

MAX_ATTEMPTS = 5
LOCK_SECONDS = 900
FAILURE_CACHE_PREFIX = 'login_fail:'


def _cache_key(username: str, ip: str) -> str:
    normalized = (username or '').strip().lower()
    return f'{FAILURE_CACHE_PREFIX}{normalized}:{ip or "unknown"}'


def get_failure_count(username: str, ip: str) -> int:
    """Return current failed login count."""
    return int(cache.get(_cache_key(username, ip), 0))


def is_locked(username: str, ip: str) -> bool:
    """Whether login is temporarily locked."""
    return get_failure_count(username, ip) >= MAX_ATTEMPTS


def record_failure(username: str, ip: str) -> int:
    """Increment failure count and return new total."""
    key = _cache_key(username, ip)
    count = int(cache.get(key, 0)) + 1
    cache.set(key, count, LOCK_SECONDS)
    return count


def clear_failures(username: str, ip: str) -> None:
    """Clear failure count after successful login."""
    cache.delete(_cache_key(username, ip))
