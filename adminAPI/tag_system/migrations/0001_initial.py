# Generated migration for tag_system

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0006_product_tenant'),
        ('tenants', '0009_tenant_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='TagCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='分类名称')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='分类编码')),
                ('category_type', models.CharField(choices=[('platform', '平台级标签'), ('tenant', '商家级标签'), ('product', '商品级标签')], max_length=20, verbose_name='分类类型')),
                ('sort_order', models.IntegerField(default=0, verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
            ],
            options={
                'verbose_name': '标签分类',
                'verbose_name_plural': '标签分类',
                'db_table': 'tag_system_category',
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='标签名称')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='标签编码')),
                ('color', models.CharField(default='#FF6B35', max_length=20, verbose_name='背景色')),
                ('text_color', models.CharField(default='#FFFFFF', max_length=20, verbose_name='文字色')),
                ('icon', models.CharField(blank=True, default='', max_length=50, verbose_name='图标')),
                ('priority', models.PositiveSmallIntegerField(default=50, verbose_name='优先级')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('can_tenant_use', models.BooleanField(default=True, verbose_name='商家可使用')),
                ('can_product_use', models.BooleanField(default=True, verbose_name='商品可打标')),
                ('requires_approval', models.BooleanField(default=False, verbose_name='需要审核')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='tag_system.tagcategory', verbose_name='所属分类')),
            ],
            options={
                'verbose_name': '促销标签',
                'verbose_name_plural': '促销标签',
                'db_table': 'tag_system_tag',
                'ordering': ['-priority', 'id'],
            },
        ),
        migrations.CreateModel(
            name='TenantTagConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_participating', models.BooleanField(default=False, verbose_name='是否参与')),
                ('custom_name', models.CharField(blank=True, default='', max_length=50, verbose_name='自定义名称')),
                ('rules', models.JSONField(blank=True, default=dict, verbose_name='规则')),
                ('start_time', models.DateTimeField(blank=True, null=True, verbose_name='开始时间')),
                ('end_time', models.DateTimeField(blank=True, null=True, verbose_name='结束时间')),
                ('status', models.CharField(choices=[('pending', '待审核'), ('approved', '已通过'), ('rejected', '已驳回')], default='approved', max_length=20, verbose_name='审核状态')),
                ('reject_reason', models.TextField(blank=True, default='', verbose_name='驳回原因')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tenant_configs', to='tag_system.tag', verbose_name='标签')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tag_configs', to='tenants.tenant', verbose_name='商家')),
            ],
            options={
                'verbose_name': '商家标签配置',
                'verbose_name_plural': '商家标签配置',
                'db_table': 'tag_system_tenant_config',
                'unique_together': {('tenant', 'tag')},
            },
        ),
        migrations.CreateModel(
            name='ProductTagConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=False, verbose_name='是否打标')),
                ('display_text', models.CharField(blank=True, default='', max_length=50, verbose_name='展示文案')),
                ('source_type', models.CharField(choices=[('platform', '平台'), ('tenant', '商家'), ('auto', '系统自动')], default='tenant', max_length=20, verbose_name='来源')),
                ('start_time', models.DateTimeField(blank=True, null=True, verbose_name='开始时间')),
                ('end_time', models.DateTimeField(blank=True, null=True, verbose_name='结束时间')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tag_configs', to='products.product', verbose_name='商品')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_configs', to='tag_system.tag', verbose_name='标签')),
            ],
            options={
                'verbose_name': '商品标签配置',
                'verbose_name_plural': '商品标签配置',
                'db_table': 'tag_system_product_config',
                'unique_together': {('product', 'tag')},
            },
        ),
    ]
