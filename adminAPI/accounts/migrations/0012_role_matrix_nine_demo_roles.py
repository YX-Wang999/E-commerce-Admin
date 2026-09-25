"""Refresh role matrix and add dept_manager / employee roles."""

from django.db import migrations

from accounts.rbac_seed import seed_default_roles_migration


class Migration(migrations.Migration):
    """Apply nine-role permission matrix."""

    dependencies = [
        ('accounts', '0011_promotion_groupbuy_coupon'),
        ('rbac', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_default_roles_migration, migrations.RunPython.noop),
    ]
