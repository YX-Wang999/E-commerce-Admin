# Generated manually

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0005_tenant_top_level_nav'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TenantAppealMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sender_type', models.CharField(choices=[('platform', '平台'), ('merchant', '商户')], max_length=20, verbose_name='发送方')),
                ('content', models.TextField(verbose_name='内容')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='发送时间')),
                ('appeal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='tenants.tenantappeal', verbose_name='申诉')),
                ('sender_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tenant_appeal_messages', to=settings.AUTH_USER_MODEL, verbose_name='发送人')),
            ],
            options={
                'verbose_name': '申诉消息',
                'verbose_name_plural': '申诉消息',
                'db_table': 'tenants_appeal_message',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='TenantInboxMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_type', models.CharField(choices=[('appeal_reply', '申诉回复'), ('system', '系统通知')], max_length=32, verbose_name='类型')),
                ('title', models.CharField(max_length=200, verbose_name='标题')),
                ('content', models.TextField(verbose_name='内容')),
                ('is_read', models.BooleanField(default=False, verbose_name='已读')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('appeal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inbox_messages', to='tenants.tenantappeal', verbose_name='关联申诉')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inbox_messages', to='tenants.tenant', verbose_name='商家')),
            ],
            options={
                'verbose_name': '商户站内信',
                'verbose_name_plural': '商户站内信',
                'db_table': 'tenants_inbox_message',
                'ordering': ['-created_at'],
            },
        ),
    ]
