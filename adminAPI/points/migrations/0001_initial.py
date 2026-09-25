# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PointsRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=32, unique=True, verbose_name='规则编码')),
                ('name', models.CharField(max_length=64, verbose_name='规则名称')),
                ('points_value', models.PositiveIntegerField(default=0, verbose_name='积分值')),
                ('description', models.CharField(blank=True, default='', max_length=255, verbose_name='说明')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '积分规则',
                'verbose_name_plural': '积分规则',
                'db_table': 'points_rule',
            },
        ),
        migrations.CreateModel(
            name='PointsAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.PositiveIntegerField(default=0, verbose_name='可用积分')),
                ('total_earned', models.PositiveIntegerField(default=0, verbose_name='累计获得')),
                ('total_spent', models.PositiveIntegerField(default=0, verbose_name='累计消耗')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('customer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='points_account', to='customers.customer', verbose_name='会员')),
            ],
            options={
                'verbose_name': '积分账户',
                'verbose_name_plural': '积分账户',
                'db_table': 'points_account',
            },
        ),
        migrations.CreateModel(
            name='PointsSignInRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sign_date', models.DateField(verbose_name='签到日期')),
                ('consecutive_days', models.PositiveIntegerField(default=1, verbose_name='连续签到天数')),
                ('points_earned', models.PositiveIntegerField(default=0, verbose_name='获得积分')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sign_in_records', to='customers.customer', verbose_name='会员')),
            ],
            options={
                'verbose_name': '签到记录',
                'verbose_name_plural': '签到记录',
                'db_table': 'points_sign_in_record',
                'unique_together': {('customer', 'sign_date')},
            },
        ),
        migrations.CreateModel(
            name='PointsTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField(verbose_name='变动数量')),
                ('balance_after', models.PositiveIntegerField(verbose_name='变动后余额')),
                ('trans_type', models.CharField(choices=[('earn_sign_in', '签到奖励'), ('earn_order', '订单奖励'), ('earn_review', '评价奖励'), ('spend_redeem', '积分兑换'), ('adjust_admin', '管理员调整')], max_length=32, verbose_name='类型')),
                ('source', models.CharField(blank=True, default='', max_length=64, verbose_name='来源标识')),
                ('description', models.CharField(blank=True, default='', max_length=255, verbose_name='描述')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='points_transactions', to='customers.customer', verbose_name='会员')),
            ],
            options={
                'verbose_name': '积分流水',
                'verbose_name_plural': '积分流水',
                'db_table': 'points_transaction',
                'ordering': ['-id'],
                'indexes': [models.Index(fields=['customer', '-created_at'], name='points_tran_custome_6f0d0d_idx'), models.Index(fields=['source'], name='points_tran_source_0d8f0a_idx')],
            },
        ),
    ]
