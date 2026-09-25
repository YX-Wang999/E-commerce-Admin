"""Upload filename helpers."""

from __future__ import annotations

import os
import random
import time


def generate_upload_filename(original_filename: str) -> str:
    """Build a unique stored filename to avoid browser cache collisions."""
    ext = os.path.splitext(original_filename or '')[1].lower()
    if ext not in {'.jpg', '.jpeg', '.png', '.gif', '.webp'}:
        ext = '.jpg'
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
    return f'{timestamp}_{random_str}{ext}'
