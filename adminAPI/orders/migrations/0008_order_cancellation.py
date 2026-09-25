# Generated manually for order cancellation feature

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_order_promotion_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='cancel_status',
            field=models.CharField(
                blank=True,
                choices=[
                    ('', '无'),
                    ('pending', '取消审核中'),
                    ('rejected', '取消已驳回'),
                ],
                default='',
                max_length=16,
                verbose_name='取消审核状态',
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='cancel_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('user', '用户取消'),
                    ('timeout', '超时取消'),
                    ('merchant', '商户取消'),
                    ('platform', '平台取消'),
                    ('groupbuy', '团购失败'),
                ],
                default='',
                max_length=16,
                verbose_name='取消类型',
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='cancel_reason',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='取消原因'),
        ),
        migrations.AddField(
            model_name='order',
            name='cancel_detail',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='取消说明'),
        ),
        migrations.AddField(
            model_name='order',
            name='cancel_review_remark',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='取消审核备注'),
        ),
        migrations.AddField(
            model_name='order',
            name='cancelled_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='取消时间'),
        ),
        migrations.CreateModel(
            name='CancelLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'action',
                    models.CharField(
                        choices=[
                            ('auto', '系统自动'),
                            ('user_direct', '用户直接取消'),
                            ('user_apply', '用户申请取消'),
                            ('merchant_approve', '商户同意取消'),
                            ('merchant_reject', '商户驳回取消'),
                            ('merchant_cancel', '商户主动取消'),
                            ('platform_cancel', '平台强制取消'),
                        ],
                        max_length=32,
                        verbose_name='操作类型',
                    ),
                ),
                ('reason', models.CharField(blank=True, default='', max_length=255, verbose_name='原因')),
                ('remark', models.CharField(blank=True, default='', max_length=255, verbose_name='备注')),
                (
                    'operator_type',
                    models.CharField(
                        choices=[
                            ('customer', '用户'),
                            ('merchant', '商户'),
                            ('staff', '平台'),
                            ('system', '系统'),
                        ],
                        max_length=16,
                        verbose_name='操作方',
                    ),
                ),
                ('operator_id', models.CharField(blank=True, default='', max_length=64, verbose_name='操作人ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                (
                    'order',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='cancel_logs',
                        to='orders.order',
                        verbose_name='订单',
                    ),
                ),
            ],
            options={
                'verbose_name': '取消日志',
                'verbose_name_plural': '取消日志',
                'db_table': 'orders_cancel_log',
                'ordering': ['-id'],
            },
        ),
    ]
