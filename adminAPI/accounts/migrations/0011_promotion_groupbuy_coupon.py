"""Update roles for group buy and coupon modules."""

from django.db import migrations

from accounts.rbac_seed import seed_default_roles_migration


class Migration(migrations.Migration):
    """Apply group buy and coupon permissions to roles."""

    dependencies = [
        ('accounts', '0010_promotion_permissions'),
        ('promotion', '0002_coupon_groupbuyactivity_usercoupon_grouporder'),
    ]

    operations = [
        migrations.RunPython(seed_default_roles_migration, migrations.RunPython.noop),
    ]
