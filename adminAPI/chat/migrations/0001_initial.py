"""Initial chat models migration."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', '待分配'), ('active', '进行中'), ('closed', '已关闭')], default='pending', max_length=20, verbose_name='状态')),
                ('user_unread_count', models.PositiveIntegerField(default=0, verbose_name='用户未读数')),
                ('staff_unread_count', models.PositiveIntegerField(default=0, verbose_name='客服未读数')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_conversations', to=settings.AUTH_USER_MODEL, verbose_name='负责客服')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversations', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '客服会话',
                'verbose_name_plural': '客服会话',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_staff', models.BooleanField(default=False, verbose_name='是否客服消息')),
                ('content', models.TextField(verbose_name='内容')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='已读时间')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='发送时间')),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='chat.conversation', verbose_name='会话')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_messages', to=settings.AUTH_USER_MODEL, verbose_name='发送者')),
            ],
            options={
                'verbose_name': '聊天消息',
                'verbose_name_plural': '聊天消息',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='StaffPresence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_online', models.BooleanField(default=False, verbose_name='是否在线')),
                ('last_seen', models.DateTimeField(auto_now=True, verbose_name='最后活跃')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='chat_presence', to=settings.AUTH_USER_MODEL, verbose_name='客服')),
            ],
            options={
                'verbose_name': '客服在线状态',
                'verbose_name_plural': '客服在线状态',
            },
        ),
    ]
