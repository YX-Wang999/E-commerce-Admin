"""Add receipt tracking fields to Order."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0008_order_cancellation'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='shipped_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='发货时间'),
        ),
        migrations.AddField(
            model_name='order',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='完成时间'),
        ),
        migrations.AddField(
            model_name='order',
            name='receipt_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', '无'),
                    ('normal', '正常签收'),
                    ('early', '提前签收'),
                    ('auto', '自动确认'),
                ],
                default='',
                max_length=16,
                verbose_name='签收方式',
            ),
        ),
    ]
