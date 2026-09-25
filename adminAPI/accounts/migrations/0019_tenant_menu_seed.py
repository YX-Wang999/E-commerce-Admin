"""Seed tenant permissions, menu and role matrix."""

from django.db import migrations

from tenants.tenant_seed import seed_tenant_menu_migration


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0018_customer_role'),
        ('tenants', '0002_tenant_department_actionlog'),
    ]

    operations = [
        migrations.RunPython(seed_tenant_menu_migration, migrations.RunPython.noop),
    ]
