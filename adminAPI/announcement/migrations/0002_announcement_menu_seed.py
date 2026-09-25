"""Seed announcement menu, permissions and demo data."""

from django.db import migrations

from announcement.announcement_seed import seed_announcement_migration


class Migration(migrations.Migration):
    """Add system announcement menu and RBAC."""

    dependencies = [
        ('announcement', '0001_initial'),
        ('feedback', '0002_feedback_menu_seed'),
        ('rbac', '0001_initial'),
        ('accounts', '0013_department_model'),
    ]

    operations = [
        migrations.RunPython(seed_announcement_migration, migrations.RunPython.noop),
    ]
