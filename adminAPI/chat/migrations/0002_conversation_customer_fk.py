"""Migrate chat conversation from User to Customer."""

import django.contrib.auth.hashers
import django.db.models.deletion
from django.conf import settings
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


def migrate_chat_user_to_customer(apps, schema_editor):
    Conversation = apps.get_model('chat', 'Conversation')
    Message = apps.get_model('chat', 'Message')
    User = apps.get_model('accounts', 'User')
    Customer = apps.get_model('customers', 'Customer')
    for conversation in Conversation.objects.all():
        user = User.objects.filter(pk=conversation.user_id).first()
        if not user:
            continue
        customer = get_or_create_customer_for_user(User, Customer, user)
        conversation.customer = customer
        conversation.save(update_fields=['customer_id'])
    for message in Message.objects.filter(is_staff=False):
        user = User.objects.filter(pk=message.sender_id).first()
        if not user:
            continue
        customer = get_or_create_customer_for_user(User, Customer, user)
        message.sender_customer = customer
        message.sender = None
        message.save(update_fields=['sender_customer_id', 'sender_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
        ('customers', '0002_customer_auth_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='sender_customer',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='chat_messages',
                to='customers.customer',
                verbose_name='用户发送者',
            ),
        ),
        migrations.AlterField(
            model_name='message',
            name='sender',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='chat_messages',
                to=settings.AUTH_USER_MODEL,
                verbose_name='客服发送者',
            ),
        ),
        migrations.AddField(
            model_name='conversation',
            name='customer',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='conversations',
                to='customers.customer',
                verbose_name='商城用户',
            ),
        ),
        migrations.RunPython(migrate_chat_user_to_customer, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='conversation',
            name='user',
        ),
        migrations.AlterField(
            model_name='conversation',
            name='customer',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='conversations',
                to='customers.customer',
                verbose_name='商城用户',
            ),
        ),
    ]
