"""Media URL helpers for API responses."""

from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit


def strip_url_query(url: str) -> str:
    """Remove query string from a URL or path (for storage normalization)."""
    if not url:
        return ''
    return urlsplit(url).path


def append_cache_version(url: str, version) -> str:
    """Append cache-busting query param without duplicating existing ?v=."""
    if not url:
        return ''
    parts = urlsplit(url)
    base = urlunsplit((parts.scheme, parts.netloc, parts.path, '', parts.fragment))
    try:
        token = int(version) if isinstance(version, bool) else int(float(version))
    except (TypeError, ValueError):
        token = version
    return f'{base}?v={token}'


def file_field_url(field, version=None) -> str:
    """Return public URL for a Django FileField/ImageField, optionally versioned."""
    if not field:
        return ''
    return to_relative_media_url(field.url, version)


def to_relative_media_url(url: str, version=None) -> str:
    """Return site-relative /media/... URL (never backend host like 127.0.0.1:8002)."""
    if not url:
        return ''
    parts = urlsplit(url)
    path = parts.path or ''
    if '/media/' in path:
        path = path[path.index('/media/'):]
    elif path:
        clean = path.lstrip('/')
        if clean.startswith('media/'):
            path = f'/{clean}'
        else:
            from django.conf import settings

            prefix = settings.MEDIA_URL.rstrip('/')
            path = f'{prefix}/{clean}'
    if version is not None:
        return append_cache_version(path, version)
    if parts.query:
        return f'{path}?{parts.query}'
    return path
