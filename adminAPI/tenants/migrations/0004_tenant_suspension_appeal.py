# Generated manually for tenant suspension and appeal models.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def seed_appeal_menu(apps, schema_editor):
    permission_model = apps.get_model('rbac', 'Permission')
    menu_model = apps.get_model('rbac', 'Menu')
    role_model = apps.get_model('rbac', 'Role')

    permission, _ = permission_model.objects.update_or_create(
        code='tenant:appeal',
        defaults={
            'name': '申诉处理',
            'module': '商户管理',
            'action': 'appeal',
            'description': '处理商户申诉',
        },
    )
    system_dir = menu_model.objects.filter(name='System').first()
    if system_dir:
        menu_model.objects.update_or_create(
            name='TenantAppealManage',
            defaults={
                'title': '申诉管理',
                'path': '/system/appeals',
                'component': 'system/AppealList',
                'icon': 'ChatLineSquare',
                'menu_type': 'menu',
                'sort_order': 96,
                'parent': system_dir,
                'permission': permission,
                'is_visible': True,
                'is_active': True,
            },
        )
    for role_code in ('ops_director', 'super_admin'):
        role = role_model.objects.filter(code=role_code).first()
        if role:
            role.permissions.add(permission)


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0003_add_unique_tenant_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TenantSuspensionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('suspend', '暂停'), ('restore', '恢复'), ('close', '关闭')], max_length=20, verbose_name='操作')),
                ('reason', models.TextField(verbose_name='原因')),
                ('detail', models.JSONField(blank=True, default=dict, verbose_name='详细信息')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='操作时间')),
                ('operator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tenant_suspension_logs', to=settings.AUTH_USER_MODEL, verbose_name='操作人')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='suspension_logs', to='tenants.tenant', verbose_name='商家')),
            ],
            options={
                'verbose_name': '商户状态记录',
                'verbose_name_plural': '商户状态记录',
                'db_table': 'tenants_suspension_log',
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='TenantAppeal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='申诉标题')),
                ('content', models.TextField(verbose_name='申诉内容')),
                ('attachments', models.JSONField(blank=True, default=list, verbose_name='附件')),
                ('status', models.CharField(choices=[('pending', '待处理'), ('processing', '处理中'), ('resolved', '已解决'), ('rejected', '已驳回')], default='pending', max_length=20, verbose_name='状态')),
                ('reply', models.TextField(blank=True, default='', verbose_name='平台回复')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('operator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='handled_tenant_appeals', to=settings.AUTH_USER_MODEL, verbose_name='处理人')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='appeals', to='tenants.tenant', verbose_name='商家')),
            ],
            options={
                'verbose_name': '商户申诉',
                'verbose_name_plural': '商户申诉',
                'db_table': 'tenants_appeal',
                'ordering': ['-id'],
            },
        ),
        migrations.AlterField(
            model_name='tenantactionlog',
            name='action',
            field=models.CharField(
                choices=[
                    ('approve', '审核通过'),
                    ('suspend', '暂停商户'),
                    ('resume', '恢复商户'),
                    ('create', '创建商户'),
                    ('delete', '删除商户'),
                    ('close', '关闭商户'),
                ],
                max_length=20,
                verbose_name='操作类型',
            ),
        ),
        migrations.RunPython(seed_appeal_menu, migrations.RunPython.noop),
    ]
