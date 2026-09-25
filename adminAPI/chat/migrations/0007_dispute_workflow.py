# Generated manually for dispute workflow

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_reviewing_status(apps, schema_editor):
    Complaint = apps.get_model('chat', 'Complaint')
    Complaint.objects.filter(status='reviewing').update(status='platform_reviewing')


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chat', '0006_alter_conversation_unread_count_staff_and_more'),
        ('orders', '0006_order_tenant'),
    ]

    operations = [
        migrations.AddField(
            model_name='complaint',
            name='title',
            field=models.CharField(default='', max_length=200, verbose_name='标题'),
        ),
        migrations.AddField(
            model_name='complaint',
            name='merchant_reply',
            field=models.TextField(blank=True, default='', verbose_name='商户回复摘要'),
        ),
        migrations.AddField(
            model_name='complaint',
            name='merchant_replied_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='商户回复时间'),
        ),
        migrations.AddField(
            model_name='complaint',
            name='customer_satisfied',
            field=models.BooleanField(blank=True, null=True, verbose_name='用户是否满意'),
        ),
        migrations.AddField(
            model_name='complaint',
            name='customer_reviewed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='用户确认时间'),
        ),
        migrations.AddField(
            model_name='complaint',
            name='platform_decision',
            field=models.CharField(
                blank=True,
                choices=[
                    ('refund', '退款'),
                    ('partial_refund', '部分退款'),
                    ('compensation', '补偿'),
                    ('dismiss', '驳回'),
                ],
                default='',
                max_length=20,
                verbose_name='平台裁决',
            ),
        ),
        migrations.AddField(
            model_name='complaint',
            name='platform_remark',
            field=models.TextField(blank=True, default='', verbose_name='平台仲裁说明'),
        ),
        migrations.AddField(
            model_name='complaint',
            name='platform_reviewed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='平台仲裁时间'),
        ),
        migrations.AddField(
            model_name='complaint',
            name='resolution',
            field=models.TextField(blank=True, default='', verbose_name='处理结果'),
        ),
        migrations.AddField(
            model_name='complaint',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='complaint',
            name='category',
            field=models.CharField(
                choices=[
                    ('product_quality', '商品质量问题'),
                    ('shipping', '物流问题'),
                    ('service', '服务态度'),
                    ('fraud', '欺诈/虚假宣传'),
                    ('refund', '退款纠纷'),
                    ('other', '其他'),
                ],
                max_length=50,
                verbose_name='投诉类型',
            ),
        ),
        migrations.AlterField(
            model_name='complaint',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', '待处理'),
                    ('merchant_processing', '商户处理中'),
                    ('customer_review', '用户确认中'),
                    ('platform_reviewing', '平台仲裁中'),
                    ('resolved', '已解决'),
                    ('rejected', '已驳回'),
                    ('closed', '已关闭'),
                ],
                default='pending',
                max_length=30,
                verbose_name='状态',
            ),
        ),
        migrations.RunPython(migrate_reviewing_status, migrations.RunPython.noop),
        migrations.CreateModel(
            name='ComplaintMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sender_type', models.CharField(
                    choices=[('customer', '用户'), ('merchant', '商户'), ('platform', '平台')],
                    max_length=20,
                    verbose_name='发送方',
                )),
                ('sender_id', models.PositiveIntegerField(verbose_name='发送者ID')),
                ('content', models.TextField(verbose_name='内容')),
                ('attachments', models.JSONField(blank=True, default=list, verbose_name='附件')),
                ('is_internal', models.BooleanField(default=False, verbose_name='平台内部备注')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='发送时间')),
                ('complaint', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='messages',
                    to='chat.complaint',
                    verbose_name='投诉',
                )),
            ],
            options={
                'verbose_name': '投诉消息',
                'verbose_name_plural': '投诉消息',
                'db_table': 'chat_complaint_message',
                'ordering': ['created_at'],
            },
        ),
    ]
