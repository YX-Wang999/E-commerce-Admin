# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customers', '0007_customer_diamond_level'),
    ]

    operations = [
        migrations.CreateModel(
            name='MemberLevel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.PositiveSmallIntegerField(unique=True, verbose_name='等级值')),
                ('name', models.CharField(max_length=32, verbose_name='等级名称')),
                ('min_points', models.PositiveIntegerField(default=0, verbose_name='所需成长值')),
                ('discount_rate', models.PositiveSmallIntegerField(default=100, help_text='100 表示无折扣，88 表示 88 折', verbose_name='折扣率(%)')),
                ('points_multiplier', models.DecimalField(decimal_places=2, default=1.0, max_digits=4, verbose_name='积分加速倍率')),
                ('description', models.CharField(blank=True, default='', max_length=255, verbose_name='权益说明')),
                ('sort_order', models.PositiveSmallIntegerField(default=0, verbose_name='排序')),
                ('is_active', models.BooleanField(default=True, verbose_name='启用')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '会员等级',
                'verbose_name_plural': '会员等级',
                'db_table': 'membership_level',
                'ordering': ['level'],
            },
        ),
        migrations.CreateModel(
            name='MemberProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('growth_points', models.PositiveIntegerField(default=0, verbose_name='成长值')),
                ('checkin_streak', models.PositiveIntegerField(default=0, verbose_name='连续签到天数')),
                ('total_checkins', models.PositiveIntegerField(default=0, verbose_name='累计签到天数')),
                ('last_checkin_date', models.DateField(blank=True, null=True, verbose_name='最近签到日期')),
                ('level_upgraded_at', models.DateTimeField(blank=True, null=True, verbose_name='最近升级时间')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('current_level', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='members', to='membership.memberlevel', verbose_name='当前等级')),
                ('customer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='member_profile', to='customers.customer', verbose_name='客户')),
            ],
            options={
                'verbose_name': '会员档案',
                'verbose_name_plural': '会员档案',
                'db_table': 'membership_profile',
            },
        ),
        migrations.CreateModel(
            name='GrowthLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField(verbose_name='变动成长值')),
                ('balance_after', models.PositiveIntegerField(verbose_name='变动后成长值')),
                ('log_type', models.CharField(choices=[('sign_in', '签到'), ('order', '消费'), ('review', '评价'), ('profile', '完善资料'), ('level_up', '等级升级'), ('admin', '管理员调整')], max_length=16, verbose_name='类型')),
                ('description', models.CharField(blank=True, default='', max_length=255, verbose_name='说明')),
                ('source', models.CharField(blank=True, default='', max_length=64, verbose_name='来源标识')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='growth_logs', to='customers.customer', verbose_name='客户')),
            ],
            options={
                'verbose_name': '成长值明细',
                'verbose_name_plural': '成长值明细',
                'db_table': 'membership_growth_log',
                'ordering': ['-id'],
            },
        ),
    ]
