"""Message privacy utilities."""

from __future__ import annotations

import re


class MessagePrivacy:
    """Detect and desensitize sensitive content in chat messages."""

    PATTERNS = {
        'phone': re.compile(r'1[3-9]\d{9}'),
        'id_card': re.compile(r'\d{17}[\dXx]'),
        'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    }

    @staticmethod
    def desensitize(content: str) -> str:
        if not content:
            return content
        for key, pattern in MessagePrivacy.PATTERNS.items():
            if key == 'phone':
                content = pattern.sub(
                    lambda match: match.group()[:3] + '****' + match.group()[-4:],
                    content,
                )
            elif key == 'id_card':
                content = pattern.sub(
                    lambda match: match.group()[:6] + '********' + match.group()[-4:],
                    content,
                )
            elif key == 'email':
                content = pattern.sub(
                    lambda match: (
                        match.group().split('@')[0][:2]
                        + '***@'
                        + match.group().split('@')[1]
                    ),
                    content,
                )
        return content

    @staticmethod
    def is_sensitive(content: str) -> bool:
        if not content:
            return False
        return any(pattern.search(content) for pattern in MessagePrivacy.PATTERNS.values())
