"""Seed feedback menu, permissions and demo data."""

from django.db import migrations

from feedback.feedback_seed import seed_feedback_migration


class Migration(migrations.Migration):
    """Add customer feedback menu and RBAC."""

    dependencies = [
        ('feedback', '0001_initial'),
        ('accounts', '0017_navigation_v1'),
        ('rbac', '0001_initial'),
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_feedback_migration, migrations.RunPython.noop),
    ]
