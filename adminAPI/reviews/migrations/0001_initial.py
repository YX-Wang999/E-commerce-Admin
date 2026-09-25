# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('customers', '0001_initial'),
        ('orders', '0001_initial'),
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(default=5, verbose_name='评分')),
                ('content', models.TextField(max_length=500, verbose_name='评价内容')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='customers.customer', verbose_name='会员')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviews', to='orders.order', verbose_name='关联订单')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='products.product', verbose_name='商品')),
            ],
            options={
                'verbose_name': '商品评价',
                'verbose_name_plural': '商品评价',
                'db_table': 'review_product_review',
                'ordering': ['-id'],
            },
        ),
    ]
