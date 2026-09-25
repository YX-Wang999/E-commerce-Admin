from django.db import migrations

from membership.membership_seed import seed_membership_migration


class Migration(migrations.Migration):

    dependencies = [
        ('membership', '0001_initial'),
        ('rbac', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_membership_migration, migrations.RunPython.noop),
    ]
