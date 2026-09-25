# Generated manually for announcement app

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Initial announcement schema."""

    initial = True

    dependencies = [
        ('accounts', '0013_department_model'),
        ('rbac', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='标题')),
                ('content', models.TextField(verbose_name='内容')),
                ('announce_type', models.CharField(
                    choices=[
                        ('maintenance', '系统维护'),
                        ('update', '功能更新'),
                        ('notice', '重要通知'),
                        ('daily', '日常公告'),
                    ],
                    max_length=20,
                    verbose_name='公告类型',
                )),
                ('priority', models.CharField(
                    choices=[
                        ('normal', '普通'),
                        ('important', '重要'),
                        ('urgent', '紧急'),
                    ],
                    default='normal',
                    max_length=20,
                    verbose_name='优先级',
                )),
                ('scope', models.CharField(
                    choices=[
                        ('all', '全部用户'),
                        ('role', '指定角色'),
                        ('department', '指定部门'),
                    ],
                    default='all',
                    max_length=20,
                    verbose_name='发布范围',
                )),
                ('is_pinned', models.BooleanField(default=False, verbose_name='是否置顶')),
                ('effective_at', models.DateTimeField(verbose_name='生效时间')),
                ('expires_at', models.DateTimeField(verbose_name='失效时间')),
                ('status', models.CharField(
                    choices=[
                        ('draft', '草稿'),
                        ('published', '已发布'),
                        ('offline', '已下线'),
                    ],
                    default='draft',
                    max_length=20,
                    verbose_name='状态',
                )),
                ('published_at', models.DateTimeField(blank=True, null=True, verbose_name='发布时间')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                (
                    'publisher',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='published_announcements',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='发布人',
                    ),
                ),
                (
                    'target_departments',
                    models.ManyToManyField(
                        blank=True,
                        related_name='announcements',
                        to='accounts.department',
                        verbose_name='目标部门',
                    ),
                ),
                (
                    'target_roles',
                    models.ManyToManyField(
                        blank=True,
                        related_name='announcements',
                        to='rbac.role',
                        verbose_name='目标角色',
                    ),
                ),
            ],
            options={
                'verbose_name': '系统公告',
                'verbose_name_plural': '系统公告',
                'db_table': 'announcement_announcement',
                'ordering': ['-is_pinned', '-published_at', '-id'],
            },
        ),
    ]
