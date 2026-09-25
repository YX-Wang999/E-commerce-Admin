# Generated manually

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0018_customer_role'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='department',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='tenants',
                to='accounts.department',
                verbose_name='对接部门',
            ),
        ),
        migrations.CreateModel(
            name='TenantActionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(
                    choices=[
                        ('approve', '审核通过'),
                        ('suspend', '暂停商户'),
                        ('resume', '恢复商户'),
                        ('create', '创建商户'),
                        ('delete', '删除商户'),
                    ],
                    max_length=20,
                    verbose_name='操作类型',
                )),
                ('remark', models.CharField(blank=True, default='', max_length=255, verbose_name='备注')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='操作时间')),
                ('operator', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='tenant_action_logs',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='操作人',
                )),
                ('tenant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='action_logs',
                    to='tenants.tenant',
                    verbose_name='商家',
                )),
            ],
            options={
                'verbose_name': '商户操作记录',
                'verbose_name_plural': '商户操作记录',
                'db_table': 'tenants_action_log',
                'ordering': ['-id'],
            },
        ),
    ]
