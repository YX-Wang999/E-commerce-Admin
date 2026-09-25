# Generated manually for addresses app

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, verbose_name='收件人')),
                ('phone', models.CharField(max_length=20, verbose_name='手机号')),
                ('province', models.CharField(max_length=64, verbose_name='省')),
                ('city', models.CharField(max_length=64, verbose_name='市')),
                ('district', models.CharField(max_length=64, verbose_name='区')),
                ('detail', models.CharField(max_length=255, verbose_name='详细地址')),
                ('is_default', models.BooleanField(default=False, verbose_name='是否默认')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '收货地址',
                'verbose_name_plural': '收货地址',
                'db_table': 'addresses_address',
                'ordering': ['-is_default', '-id'],
            },
        ),
    ]
