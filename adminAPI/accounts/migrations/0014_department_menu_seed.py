"""Seed department permissions, menu and refresh role matrix."""

from django.db import migrations

from accounts.department_seed import seed_department_menu_migration


class Migration(migrations.Migration):
    """Add department management menu and permissions."""

    dependencies = [
        ('accounts', '0013_department_model'),
        ('rbac', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_department_menu_migration, migrations.RunPython.noop),
    ]
