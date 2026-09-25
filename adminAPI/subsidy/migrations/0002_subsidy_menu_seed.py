from django.db import migrations

from subsidy.subsidy_seed import seed_subsidy_migration


class Migration(migrations.Migration):
    dependencies = [
        ('subsidy', '0001_initial'),
        ('rbac', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_subsidy_migration, migrations.RunPython.noop),
    ]
