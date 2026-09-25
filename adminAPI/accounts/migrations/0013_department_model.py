"""Add Department model and user department FK."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Create departments and link users."""

    dependencies = [
        ('accounts', '0012_role_matrix_nine_demo_roles'),
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, verbose_name='部门名称')),
                ('code', models.CharField(max_length=32, unique=True, verbose_name='部门编码')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                (
                    'manager',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='managed_departments',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='部门经理',
                    ),
                ),
                (
                    'parent',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='children',
                        to='accounts.department',
                        verbose_name='上级部门',
                    ),
                ),
            ],
            options={
                'verbose_name': '部门',
                'verbose_name_plural': '部门',
                'db_table': 'accounts_department',
                'ordering': ['id'],
            },
        ),
        migrations.AddField(
            model_name='user',
            name='department',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='members',
                to='accounts.department',
                verbose_name='所属部门',
            ),
        ),
    ]
