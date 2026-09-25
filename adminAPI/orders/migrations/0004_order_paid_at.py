"""Add paid_at to Order."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_orderitem_product_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='支付时间'),
        ),
    ]
