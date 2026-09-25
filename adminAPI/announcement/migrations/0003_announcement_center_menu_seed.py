"""Seed announcement center menu under system management."""

from django.db import migrations


def seed_announcement_center_menu(apps, schema_editor) -> None:
    menu_model = apps.get_model('rbac', 'Menu')
    permission_model = apps.get_model('rbac', 'Permission')
    system_dir = menu_model.objects.filter(name='System').first()
    permission = permission_model.objects.filter(code='announcement:read').first()
    if not system_dir:
        return
    menu_model.objects.update_or_create(
        name='AnnouncementCenter',
        defaults={
            'title': '公告中心',
            'path': '/announcements',
            'component': 'announcements/AnnouncementCenter',
            'icon': 'Notification',
            'menu_type': 'menu',
            'sort_order': 97,
            'parent': system_dir,
            'permission': permission,
            'is_visible': True,
            'is_active': True,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ('announcement', '0002_announcement_menu_seed'),
    ]

    operations = [
        migrations.RunPython(seed_announcement_center_menu, migrations.RunPython.noop),
    ]
