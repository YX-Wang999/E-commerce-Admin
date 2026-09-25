"""Backfill PointsAccount for existing customers."""

from django.db import migrations


def backfill_points_accounts(apps, schema_editor):
    Customer = apps.get_model('customers', 'Customer')
    PointsAccount = apps.get_model('points', 'PointsAccount')
    for customer in Customer.objects.all().iterator():
        PointsAccount.objects.get_or_create(
            customer=customer,
            defaults={
                'balance': customer.points,
                'total_earned': customer.points,
                'total_spent': 0,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('points', '0002_points_menu_seed'),
        ('customers', '0002_customer_auth_fields'),
    ]

    operations = [
        migrations.RunPython(backfill_points_accounts, migrations.RunPython.noop),
    ]
