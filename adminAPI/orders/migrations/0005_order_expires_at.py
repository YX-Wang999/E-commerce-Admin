"""Add expires_at to Order."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_order_paid_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='支付截止时间'),
        ),
    ]
