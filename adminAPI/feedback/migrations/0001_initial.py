# Generated manually for feedback app

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Initial feedback schema."""

    initial = True

    dependencies = [
        ('customers', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nickname', models.CharField(max_length=50, verbose_name='客户昵称')),
                ('phone', models.CharField(max_length=20, verbose_name='联系方式')),
                ('feedback_type', models.CharField(
                    choices=[
                        ('complaint', '投诉'),
                        ('suggestion', '建议'),
                        ('inquiry', '咨询'),
                        ('after_sales', '售后'),
                    ],
                    max_length=20,
                    verbose_name='留言类型',
                )),
                ('content', models.TextField(max_length=500, verbose_name='留言内容')),
                ('images', models.JSONField(blank=True, default=list, verbose_name='图片列表')),
                ('status', models.CharField(
                    choices=[
                        ('pending', '待处理'),
                        ('processing', '处理中'),
                        ('done', '已处理'),
                        ('closed', '已关闭'),
                    ],
                    default='pending',
                    max_length=20,
                    verbose_name='状态',
                )),
                ('handler_remark', models.TextField(blank=True, default='', verbose_name='处理备注')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('handled_at', models.DateTimeField(blank=True, null=True, verbose_name='处理时间')),
                (
                    'customer',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='feedbacks',
                        to='customers.customer',
                        verbose_name='关联会员',
                    ),
                ),
                (
                    'handler',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='handled_feedbacks',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='处理人',
                    ),
                ),
            ],
            options={
                'verbose_name': '客户留言',
                'verbose_name_plural': '客户留言',
                'db_table': 'feedback_customer_feedback',
                'ordering': ['-id'],
            },
        ),
    ]
