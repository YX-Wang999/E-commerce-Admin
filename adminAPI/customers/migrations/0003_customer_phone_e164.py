# Generated manually

from django.db import migrations, models


def _normalize_phones(apps, schema_editor):
    Customer = apps.get_model('customers', 'Customer')
    for customer in Customer.objects.all().iterator():
        phone = (customer.phone or '').strip()
        if phone and not phone.startswith('+') and len(phone) == 11 and phone.startswith('1'):
            customer.phone = f'+86{phone}'
            customer.save(update_fields=['phone'])


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0002_customer_auth_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='phone',
            field=models.CharField(max_length=32, unique=True, verbose_name='手机号'),
        ),
        migrations.RunPython(_normalize_phones, migrations.RunPython.noop),
    ]
