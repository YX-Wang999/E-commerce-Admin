"""Seed points menu, permissions and rules."""

from django.db import migrations

from points.points_seed import seed_points_migration


class Migration(migrations.Migration):
    dependencies = [
        ('points', '0001_initial'),
        ('announcement', '0002_announcement_menu_seed'),
        ('rbac', '0001_initial'),
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_points_migration, migrations.RunPython.noop),
    ]
