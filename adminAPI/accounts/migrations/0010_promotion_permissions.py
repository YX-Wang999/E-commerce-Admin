"""Update role permissions for promotion seckill module."""

from django.db import migrations

from accounts.rbac_seed import seed_default_roles_migration


class Migration(migrations.Migration):
    """Apply promotion permissions and ops_director role."""

    dependencies = [
        ('accounts', '0009_inventory_log_permissions'),
        ('promotion', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_default_roles_migration, migrations.RunPython.noop),
    ]
