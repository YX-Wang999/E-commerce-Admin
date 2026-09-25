"""Seed default RBAC roles."""

from django.db import migrations

from accounts.rbac_seed import seed_default_roles_migration


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_add_activation_log'),
        ('rbac', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            seed_default_roles_migration,
            migrations.RunPython.noop,
        ),
    ]
