"""Push announcement notifications via WebSocket."""

from __future__ import annotations

from announcement.models import Announcement
from tenants.notify import push_admin_alert


def notify_announcement_published(announcement: Announcement) -> None:
    push_admin_alert(
        {
            'type': 'announcement',
            'level': 'urgent' if announcement.priority == Announcement.PRIORITY_URGENT else 'info',
            'title': f'【公告】{announcement.title}',
            'content': announcement.content[:200],
            'target_url': '/announcements',
            'announcement_id': announcement.id,
            'is_pinned': announcement.is_pinned,
            'priority': announcement.priority,
        },
    )
