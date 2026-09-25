# Generated manually for cart app

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('products', '0005_category_icon'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cart', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '购物车',
                'verbose_name_plural': '购物车',
                'db_table': 'cart_cart',
            },
        ),
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='数量')),
                ('selected', models.BooleanField(default=True, verbose_name='是否选中')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('cart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='cart.cart', verbose_name='购物车')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='products.product', verbose_name='商品')),
            ],
            options={
                'verbose_name': '购物车商品',
                'verbose_name_plural': '购物车商品',
                'db_table': 'cart_cart_item',
                'unique_together': {('cart', 'product')},
            },
        ),
    ]
