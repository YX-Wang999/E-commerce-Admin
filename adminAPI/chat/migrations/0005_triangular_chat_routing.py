# Generated manually for triangular chat routing.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def backfill_conversation_types(apps, schema_editor):
    Conversation = apps.get_model('chat', 'Conversation')
    for conv in Conversation.objects.all():
        if conv.tenant_id and conv.user_id:
            conv.conversation_type = 'b2c'
        elif conv.tenant_id and not conv.user_id:
            conv.conversation_type = 'b2p'
        elif conv.user_id:
            conv.conversation_type = 'c2p'
        else:
            conv.conversation_type = 'c2p'
        conv.save(update_fields=['conversation_type'])


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0004_rename_customer_conversation_user_and_more'),
        ('customers', '0001_initial'),
        ('orders', '0001_initial'),
        ('tenants', '0003_add_unique_tenant_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='Complaint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('product_quality', '商品质量'), ('shipping', '物流问题'), ('service', '服务态度'), ('fraud', '欺诈行为'), ('other', '其他')], max_length=50, verbose_name='投诉类型')),
                ('content', models.TextField(verbose_name='投诉内容')),
                ('attachments', models.JSONField(blank=True, default=list, verbose_name='附件')),
                ('status', models.CharField(choices=[('pending', '待审核'), ('reviewing', '审核中'), ('resolved', '已解决'), ('rejected', '已驳回')], default='pending', max_length=20, verbose_name='状态')),
                ('platform_reply', models.TextField(blank=True, default='', verbose_name='平台回复')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('resolved_at', models.DateTimeField(blank=True, null=True, verbose_name='处理时间')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='complaints', to='customers.customer', verbose_name='客户')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='complaints', to='orders.order', verbose_name='关联订单')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_complaints', to=settings.AUTH_USER_MODEL, verbose_name='处理人')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='complaints', to='tenants.tenant', verbose_name='被投诉商户')),
            ],
            options={
                'verbose_name': '商户投诉',
                'verbose_name_plural': '商户投诉',
                'db_table': 'chat_complaint',
                'ordering': ['-id'],
            },
        ),
        migrations.RemoveConstraint(
            model_name='conversation',
            name='chat_unique_active_conversation_per_tenant_user',
        ),
        migrations.AddField(
            model_name='conversation',
            name='complaint',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='conversations', to='chat.complaint', verbose_name='关联投诉'),
        ),
        migrations.AddField(
            model_name='conversation',
            name='conversation_type',
            field=models.CharField(
                choices=[
                    ('b2c', '商户→客户'),
                    ('c2p', '客户→平台'),
                    ('b2p', '商户→平台'),
                    ('p2b', '平台→商户'),
                    ('c2p_b', '客户投诉商户'),
                ],
                default='c2p',
                max_length=20,
                verbose_name='会话类型',
            ),
        ),
        migrations.AlterField(
            model_name='conversation',
            name='user',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='conversations',
                to='customers.customer',
                verbose_name='商城用户',
            ),
        ),
        migrations.RunPython(backfill_conversation_types, migrations.RunPython.noop),
    ]
