"""Seed org chart menu, permission and demo supervisors."""

from django.db import migrations

from accounts.org_seed import seed_org_chart_migration


class Migration(migrations.Migration):
    """Add organization chart menu and wire demo hierarchy."""

    dependencies = [
        ('accounts', '0015_user_supervisor'),
        ('rbac', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_org_chart_migration, migrations.RunPython.noop),
    ]
