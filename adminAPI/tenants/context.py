"""Thread-local current tenant for ORM managers."""

from __future__ import annotations

import threading

_thread_locals = threading.local()


def get_current_tenant():
    """Return tenant bound to the current request thread."""
    return getattr(_thread_locals, 'tenant', None)


def set_current_tenant(tenant) -> None:
    _thread_locals.tenant = tenant


def clear_current_tenant() -> None:
    if hasattr(_thread_locals, 'tenant'):
        del _thread_locals.tenant
