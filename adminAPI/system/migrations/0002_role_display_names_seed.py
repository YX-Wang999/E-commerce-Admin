"""Seed role_display_names system setting."""

import json

from django.db import migrations


def seed_role_display_names(apps, schema_editor):
    SystemSetting = apps.get_model('system', 'SystemSetting')
    SystemSetting.objects.get_or_create(
        key='role_display_names',
        defaults={
            'value': '{}',
            'value_type': 'string',
            'description': '角色多语言显示名称（JSON）',
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0001_initial'),
        ('rbac', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_role_display_names, migrations.RunPython.noop),
    ]
