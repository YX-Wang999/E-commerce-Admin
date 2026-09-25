"""Seed customer role for mall registration."""

from django.db import migrations

from accounts.rbac_seed import seed_default_roles_migration


class Migration(migrations.Migration):
    """Add customer role to default RBAC matrix."""

    dependencies = [
        ('accounts', '0017_navigation_v1'),
    ]

    operations = [
        migrations.RunPython(seed_default_roles_migration, migrations.RunPython.noop),
    ]
