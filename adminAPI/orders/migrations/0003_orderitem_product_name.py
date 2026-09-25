# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_order_assigned_to'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='product_name',
            field=models.CharField(blank=True, default='', max_length=128, verbose_name='商品名称快照'),
        ),
    ]
