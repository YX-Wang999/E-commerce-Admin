"""Migrate address from User to Customer."""

import django.contrib.auth.hashers
import django.db.models.deletion
from django.db import migrations, models


def get_or_create_customer_for_user(User, Customer, user):
    phone = (user.phone or '').strip()
    if not phone:
        phone = f'U{user.id:08d}'
    customer, created = Customer.objects.get_or_create(
        phone=phone,
        defaults={
            'name': user.nickname or user.username,
            'nickname': user.nickname or user.username,
            'email': user.email or '',
            'password': django.contrib.auth.hashers.make_password('changeme123'),
            'is_active': user.is_active,
        },
    )
    if not created and not customer.password:
        customer.password = django.contrib.auth.hashers.make_password('changeme123')
        customer.save(update_fields=['password'])
    return customer


def migrate_address_user_to_customer(apps, schema_editor):
    Address = apps.get_model('addresses', 'Address')
    User = apps.get_model('accounts', 'User')
    Customer = apps.get_model('customers', 'Customer')
    for address in Address.objects.all():
        user = User.objects.filter(pk=address.user_id).first()
        if not user:
            continue
        address.customer = get_or_create_customer_for_user(User, Customer, user)
        address.save(update_fields=['customer_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('addresses', '0001_initial'),
        ('customers', '0002_customer_auth_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='customer',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='addresses',
                to='customers.customer',
                verbose_name='商城用户',
            ),
        ),
        migrations.RunPython(migrate_address_user_to_customer, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='address',
            name='user',
        ),
        migrations.AlterField(
            model_name='address',
            name='customer',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='addresses',
                to='customers.customer',
                verbose_name='商城用户',
            ),
        ),
    ]
