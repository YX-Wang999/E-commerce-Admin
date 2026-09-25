# Generated manually

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0009_tenant_description'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ClosureApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.CharField(max_length=200, verbose_name='注销原因')),
                ('detail', models.TextField(blank=True, default='', verbose_name='详细说明')),
                ('attachments', models.JSONField(blank=True, default=list, verbose_name='附件')),
                ('status', models.CharField(choices=[('pending', '待审核'), ('approved', '审核通过'), ('rejected', '审核驳回'), ('notice_period', '公示期'), ('completed', '已注销'), ('cancelled', '已取消')], default='pending', max_length=20, verbose_name='状态')),
                ('reviewed_at', models.DateTimeField(blank=True, null=True, verbose_name='审核时间')),
                ('reject_reason', models.TextField(blank=True, default='', verbose_name='驳回原因')),
                ('notice_start_at', models.DateTimeField(blank=True, null=True, verbose_name='公示开始时间')),
                ('notice_end_at', models.DateTimeField(blank=True, null=True, verbose_name='公示结束时间')),
                ('notice_days', models.PositiveIntegerField(default=15, verbose_name='公示天数')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='注销完成时间')),
                ('data_exported_at', models.DateTimeField(blank=True, null=True, verbose_name='数据导出时间')),
                ('data_export_url', models.URLField(blank=True, default='', max_length=500, verbose_name='数据下载链接')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='申请时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_closure_applications', to=settings.AUTH_USER_MODEL, verbose_name='审核人')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='closure_applications', to='tenants.tenant', verbose_name='商家')),
            ],
            options={
                'verbose_name': '店铺注销申请',
                'verbose_name_plural': '店铺注销申请',
                'db_table': 'shop_closure_application',
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='ClosureNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipient', models.CharField(max_length=200, verbose_name='接收方')),
                ('channel', models.CharField(choices=[('email', '邮件'), ('sms', '短信'), ('in_app', '站内信')], max_length=20, verbose_name='渠道')),
                ('content', models.TextField(verbose_name='内容')),
                ('sent_at', models.DateTimeField(auto_now_add=True, verbose_name='发送时间')),
                ('is_delivered', models.BooleanField(default=False, verbose_name='是否送达')),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='shop_closure.closureapplication', verbose_name='申请')),
            ],
            options={
                'verbose_name': '注销通知',
                'verbose_name_plural': '注销通知',
                'db_table': 'shop_closure_notification',
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='ClosureChecklist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item', models.CharField(max_length=100, verbose_name='检查项')),
                ('code', models.CharField(max_length=50, verbose_name='检查编码')),
                ('is_completed', models.BooleanField(default=False, verbose_name='是否完成')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='完成时间')),
                ('remark', models.TextField(blank=True, default='', verbose_name='备注')),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='checklist', to='shop_closure.closureapplication', verbose_name='申请')),
            ],
            options={
                'verbose_name': '注销检查清单',
                'verbose_name_plural': '注销检查清单',
                'db_table': 'shop_closure_checklist',
                'unique_together': {('application', 'code')},
            },
        ),
    ]
