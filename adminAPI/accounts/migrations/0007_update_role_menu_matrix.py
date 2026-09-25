"""Update role-menu matrix per company policy."""

from django.db import migrations

from accounts.rbac_seed import seed_default_roles_migration


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_seed_default_roles'),
    ]

    operations = [
        migrations.RunPython(
            seed_default_roles_migration,
            migrations.RunPython.noop,
        ),
    ]
