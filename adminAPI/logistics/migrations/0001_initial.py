# Generated manually for logistics MVP

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('orders', '0006_order_tenant'),
    ]

    operations = [
        migrations.CreateModel(
            name='Logistics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('express_company', models.CharField(max_length=50, verbose_name='快递公司')),
                ('express_code', models.CharField(max_length=20, verbose_name='快递公司编码')),
                ('tracking_number', models.CharField(max_length=100, verbose_name='物流单号')),
                ('status', models.CharField(
                    choices=[
                        ('pending', '待发货'),
                        ('picked', '已揽收'),
                        ('transporting', '运输中'),
                        ('delivering', '派送中'),
                        ('delivered', '已签收'),
                        ('exception', '异常'),
                        ('returned', '已退回'),
                    ],
                    default='pending',
                    max_length=20,
                    verbose_name='物流状态',
                )),
                ('traces', models.JSONField(blank=True, default=list, verbose_name='轨迹')),
                ('raw_response', models.JSONField(blank=True, default=dict, verbose_name='原始响应')),
                ('picked_at', models.DateTimeField(blank=True, null=True, verbose_name='揽收时间')),
                ('delivered_at', models.DateTimeField(blank=True, null=True, verbose_name='签收时间')),
                ('last_trace_at', models.DateTimeField(blank=True, null=True, verbose_name='最后轨迹时间')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('order', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='logistics',
                    to='orders.order',
                    verbose_name='订单',
                )),
            ],
            options={
                'verbose_name': '物流信息',
                'verbose_name_plural': '物流信息',
                'db_table': 'logistics_logistics',
            },
        ),
    ]
