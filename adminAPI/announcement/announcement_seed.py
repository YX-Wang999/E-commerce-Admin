"""Announcement permissions, menu and demo data seed."""

from datetime import timedelta
from typing import Any

from django.utils import timezone

ANNOUNCEMENT_PERMISSIONS: list[tuple[str, str, str, str]] = [
    ('公告查看', 'announcement:read', '系统公告', 'read'),
    ('公告新增', 'announcement:create', '系统公告', 'create'),
    ('公告修改', 'announcement:update', '系统公告', 'update'),
    ('公告删除', 'announcement:delete', '系统公告', 'delete'),
    ('公告发布', 'announcement:publish', '系统公告', 'publish'),
]


def seed_announcement_permissions(permission_model: Any) -> dict[str, Any]:
    """Create announcement permissions."""
    permissions: dict[str, Any] = {}
    for name, code, module, action in ANNOUNCEMENT_PERMISSIONS:
        permission, _ = permission_model.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'module': module,
                'action': action,
                'description': name,
            },
        )
        permissions[code] = permission
    return permissions


def seed_announcement_menu(menu_model: Any, system_dir: Any, permissions: dict[str, Any]) -> Any:
    """Create system announcement menu."""
    menu, _ = menu_model.objects.update_or_create(
        name='AnnouncementList',
        defaults={
            'title': '系统公告',
            'path': '/system/announcement',
            'component': 'system/AnnouncementList',
            'icon': 'Bell',
            'menu_type': 'menu',
            'sort_order': 96,
            'parent': system_dir,
            'permission': permissions.get('announcement:read'),
            'is_visible': True,
            'is_active': True,
        },
    )
    return menu


def seed_announcement_center_menu(menu_model: Any, system_dir: Any, permissions: dict[str, Any]) -> Any:
    """Create announcement center menu under system management."""
    menu, _ = menu_model.objects.update_or_create(
        name='AnnouncementCenter',
        defaults={
            'title': '公告中心',
            'path': '/announcements',
            'component': 'announcements/AnnouncementCenter',
            'icon': 'Notification',
            'menu_type': 'menu',
            'sort_order': 97,
            'parent': system_dir,
            'permission': permissions.get('announcement:read'),
            'is_visible': True,
            'is_active': True,
        },
    )
    return menu


def seed_demo_announcements(announcement_model: Any, user_model: Any) -> None:
    """Seed demo announcements."""
    admin_user = user_model.objects.filter(username='admin').first()
    now = timezone.now()
    demos = [
        {
            'title': '系统维护通知',
            'content': '<p>本周六 02:00-04:00 将进行系统维护，期间可能无法访问后台，请提前安排工作。</p>',
            'announce_type': 'maintenance',
            'priority': 'urgent',
            'scope': 'all',
            'is_pinned': True,
            'status': 'published',
            'offset_start': -1,
            'offset_end': 7,
        },
        {
            'title': '客户留言功能上线',
            'content': '<p>后台已新增「客户留言」模块，客服专员可在客户管理下查看并回复客户留言。</p>',
            'announce_type': 'update',
            'priority': 'important',
            'scope': 'all',
            'is_pinned': False,
            'status': 'published',
            'offset_start': -2,
            'offset_end': 14,
        },
        {
            'title': '端午节放假安排',
            'content': '<p>端午节期间客服值班安排已更新，详情请查看内部通知。</p>',
            'announce_type': 'daily',
            'priority': 'normal',
            'scope': 'all',
            'is_pinned': False,
            'status': 'published',
            'offset_start': -3,
            'offset_end': 10,
        },
        {
            'title': '双十一大促筹备（草稿）',
            'content': '<p>大促活动方案待审批，暂未发布。</p>',
            'announce_type': 'notice',
            'priority': 'important',
            'scope': 'all',
            'is_pinned': False,
            'status': 'draft',
            'offset_start': 1,
            'offset_end': 30,
        },
    ]
    for item in demos:
        effective_at = now + timedelta(days=item['offset_start'])
        expires_at = now + timedelta(days=item['offset_end'])
        defaults = {
            'content': item['content'],
            'announce_type': item['announce_type'],
            'priority': item['priority'],
            'scope': item['scope'],
            'is_pinned': item['is_pinned'],
            'effective_at': effective_at,
            'expires_at': expires_at,
            'status': item['status'],
        }
        if item['status'] == 'published':
            defaults['publisher'] = admin_user
            defaults['published_at'] = now - timedelta(days=abs(item['offset_start']))
        announcement, _ = announcement_model.objects.update_or_create(
            title=item['title'],
            defaults=defaults,
        )


def seed_announcement_migration(apps, schema_editor) -> None:
    """Migration hook: announcement menu, permissions, demo data."""
    from accounts.rbac_seed import seed_default_roles_migration

    permission_model = apps.get_model('rbac', 'Permission')
    menu_model = apps.get_model('rbac', 'Menu')
    announcement_model = apps.get_model('announcement', 'Announcement')
    user_model = apps.get_model('accounts', 'User')
    permissions = seed_announcement_permissions(permission_model)
    system_dir = menu_model.objects.filter(name='System').first()
    if system_dir:
        seed_announcement_menu(menu_model, system_dir, permissions)
        seed_announcement_center_menu(menu_model, system_dir, permissions)
    seed_demo_announcements(announcement_model, user_model)
    seed_default_roles_migration(apps, schema_editor)
