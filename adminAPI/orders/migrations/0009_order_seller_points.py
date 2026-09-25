# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0008_order_cancellation'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='seller_points_discount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='商家积分抵扣'),
        ),
        migrations.AddField(
            model_name='order',
            name='seller_points_used',
            field=models.PositiveIntegerField(default=0, verbose_name='使用商家积分'),
        ),
    ]
