"""Update role permissions for inventory logs."""

from django.db import migrations

from accounts.rbac_seed import seed_default_roles_migration


class Migration(migrations.Migration):
    """Apply inventory log permissions to roles."""

    dependencies = [
        ('accounts', '0008_ecommerce_role_matrix'),
        ('products', '0003_inventorylog'),
    ]

    operations = [
        migrations.RunPython(seed_default_roles_migration, migrations.RunPython.noop),
    ]
