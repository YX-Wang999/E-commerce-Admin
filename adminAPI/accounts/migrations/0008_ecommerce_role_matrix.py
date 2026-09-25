"""Update role menu matrix for e-commerce scenario."""

from django.db import migrations

from accounts.rbac_seed import seed_default_roles_migration


class Migration(migrations.Migration):
    """Apply e-commerce role and menu bindings."""

    dependencies = [
        ('accounts', '0007_update_role_menu_matrix'),
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_default_roles_migration, migrations.RunPython.noop),
    ]
