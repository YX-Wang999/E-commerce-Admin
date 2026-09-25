"""Sync platform menus for tags, points rules and shop closure."""

from django.db import migrations


def forwards_sync_feature_menus(apps, schema_editor):
    from accounts.menu_sync import sync_all_menus

    sync_all_menus(refresh_roles=True)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0019_tenant_menu_seed'),
        ('tag_system', '0002_seed_default_tags'),
        ('points', '0008_alter_pointsrule_created_at'),
        ('shop_closure', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards_sync_feature_menus, migrations.RunPython.noop),
    ]
