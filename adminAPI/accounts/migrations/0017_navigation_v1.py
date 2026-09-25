"""Navigation v1.0: report sub-menus and logistics."""

from django.db import migrations

from accounts.navigation_seed import seed_navigation_v1_migration


class Migration(migrations.Migration):
    """Expand report and order navigation menus."""

    dependencies = [
        ('accounts', '0016_org_chart_seed'),
        ('rbac', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_navigation_v1_migration, migrations.RunPython.noop),
    ]
