"""Refactor subsidy to government filing model."""

from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models


def migrate_status_to_filing(apps, schema_editor) -> None:
    SubsidyProduct = apps.get_model('subsidy', 'SubsidyProduct')
    mapping = {
        'pending': 'submitted',
        'approved': 'approved',
        'rejected': 'rejected',
    }
    for row in SubsidyProduct.objects.all():
        old_status = getattr(row, 'status', None)
        row.filing_status = mapping.get(old_status, 'not_submitted')
        if old_status == 'pending' and not row.filing_submitted_at:
            row.filing_submitted_at = row.created_at
        reject = getattr(row, 'reject_reason', '') or ''
        if reject:
            row.filing_reject_reason = reject
        row.save(update_fields=['filing_status', 'filing_submitted_at', 'filing_reject_reason'])


def update_menus(apps, schema_editor) -> None:
    Menu = apps.get_model('rbac', 'Menu')
    Menu.objects.filter(name='SubsidyDir').update(title='国补数据监控')
    Menu.objects.filter(name='SubsidyProductReview').update(
        title='备案状态监控',
        path='/subsidy/filings',
        component='subsidy/FilingMonitorList',
    )
    Menu.objects.filter(name='SubsidyStats').update(title='订单上报统计')


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0008_order_cancellation'),
        ('subsidy', '0002_subsidy_menu_seed'),
    ]

    operations = [
        migrations.AddField(
            model_name='subsidypolicy',
            name='category',
            field=models.CharField(blank=True, default='', max_length=64, verbose_name='适用品类'),
        ),
        migrations.AddField(
            model_name='subsidypolicy',
            name='region',
            field=models.CharField(blank=True, default='', max_length=64, verbose_name='适用地区'),
        ),
        migrations.AddField(
            model_name='subsidyproduct',
            name='category',
            field=models.CharField(blank=True, default='', max_length=64, verbose_name='补贴品类'),
        ),
        migrations.AddField(
            model_name='subsidyproduct',
            name='filing_reject_reason',
            field=models.TextField(blank=True, default='', verbose_name='备案驳回原因'),
        ),
        migrations.AddField(
            model_name='subsidyproduct',
            name='filing_status',
            field=models.CharField(
                choices=[
                    ('not_submitted', '未备案'),
                    ('submitted', '已提交备案'),
                    ('approved', '已备案通过'),
                    ('rejected', '备案驳回'),
                ],
                default='not_submitted',
                max_length=20,
                verbose_name='备案状态',
            ),
        ),
        migrations.AddField(
            model_name='subsidyproduct',
            name='filing_submitted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='备案提交时间'),
        ),
        migrations.AddField(
            model_name='subsidyproduct',
            name='region',
            field=models.CharField(blank=True, default='', max_length=64, verbose_name='活动地区'),
        ),
        migrations.RunPython(migrate_status_to_filing, migrations.RunPython.noop),
        migrations.RemoveField(model_name='subsidyproduct', name='reject_reason'),
        migrations.RemoveField(model_name='subsidyproduct', name='reviewed_at'),
        migrations.RemoveField(model_name='subsidyproduct', name='reviewed_by'),
        migrations.RemoveField(model_name='subsidyproduct', name='status'),
        migrations.CreateModel(
            name='SubsidyOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sn_code', models.CharField(blank=True, default='', max_length=100, verbose_name='SN码')),
                ('imei_code', models.CharField(blank=True, default='', max_length=200, verbose_name='IMEI码')),
                ('government_status', models.CharField(
                    choices=[
                        ('pending', '待上报'),
                        ('reported', '已上报'),
                        ('verified', '核验通过'),
                        ('failed', '核验失败'),
                    ],
                    default='pending',
                    max_length=20,
                    verbose_name='政府核验状态',
                )),
                ('reported_at', models.DateTimeField(blank=True, null=True, verbose_name='上报时间')),
                ('fail_reason', models.CharField(blank=True, default='', max_length=255, verbose_name='核验失败原因')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('order', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='subsidy_order',
                    to='orders.order',
                    verbose_name='订单',
                )),
                ('tenant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='subsidy_orders',
                    to='tenants.tenant',
                    verbose_name='商家',
                )),
            ],
            options={
                'verbose_name': '国补订单',
                'verbose_name_plural': '国补订单',
                'db_table': 'subsidy_order',
                'ordering': ['-created_at'],
            },
        ),
        migrations.RunPython(update_menus, migrations.RunPython.noop),
    ]
