# Generated manually

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customers', '0001_initial'),
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SellerPointsRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('earn_rate', models.DecimalField(decimal_places=2, default=1.0, help_text='每消费1元送多少积分', max_digits=5, verbose_name='消费送积分比例')),
                ('max_earn_per_order', models.PositiveIntegerField(default=1000, verbose_name='单笔订单最大获取积分')),
                ('redeem_rate', models.DecimalField(decimal_places=2, default=100.0, help_text='多少积分抵1元', max_digits=10, verbose_name='积分兑换比例')),
                ('max_redeem_rate', models.DecimalField(decimal_places=2, default=30.0, help_text='最多可抵订单金额的百分比', max_digits=5, verbose_name='最大抵扣比例(%)')),
                ('expire_days', models.PositiveIntegerField(default=365, verbose_name='积分有效期(天)')),
                ('points_name', models.CharField(default='店铺积分', max_length=50, verbose_name='积分名称')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('tenant', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='seller_points_rule', to='tenants.tenant', verbose_name='商家')),
            ],
            options={
                'verbose_name': '商家积分规则',
                'verbose_name_plural': '商家积分规则',
                'db_table': 'seller_points_rule',
            },
        ),
        migrations.CreateModel(
            name='SellerPointsAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.PositiveIntegerField(default=0, verbose_name='当前积分余额')),
                ('total_earned', models.PositiveIntegerField(default=0, verbose_name='累计获得')),
                ('total_spent', models.PositiveIntegerField(default=0, verbose_name='累计消耗')),
                ('expire_at', models.DateTimeField(blank=True, null=True, verbose_name='积分过期时间')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seller_points_accounts', to='customers.customer', verbose_name='客户')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seller_points_accounts', to='tenants.tenant', verbose_name='商家')),
            ],
            options={
                'verbose_name': '商家积分账户',
                'verbose_name_plural': '商家积分账户',
                'db_table': 'seller_points_account',
                'unique_together': {('tenant', 'customer')},
            },
        ),
        migrations.CreateModel(
            name='SellerPointsTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField(verbose_name='变动数量')),
                ('balance_after', models.PositiveIntegerField(verbose_name='变动后余额')),
                ('trans_type', models.CharField(choices=[('earn_order', '订单奖励'), ('redeem_order', '订单抵扣'), ('expire', '过期扣除'), ('admin_adjust', '商家调整'), ('refund_order', '订单退还')], max_length=32, verbose_name='类型')),
                ('source_id', models.CharField(blank=True, default='', max_length=100, verbose_name='来源ID')),
                ('description', models.CharField(blank=True, default='', max_length=200, verbose_name='描述')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='seller_points.sellerpointsaccount', verbose_name='账户')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seller_points_transactions', to='customers.customer', verbose_name='客户')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seller_points_transactions', to='tenants.tenant', verbose_name='商家')),
            ],
            options={
                'verbose_name': '商家积分流水',
                'verbose_name_plural': '商家积分流水',
                'db_table': 'seller_points_transaction',
                'ordering': ['-id'],
                'indexes': [
                    models.Index(fields=['tenant', '-created_at'], name='seller_pts_tx_tenant_idx'),
                    models.Index(fields=['customer', '-created_at'], name='seller_pts_tx_cust_idx'),
                    models.Index(fields=['source_id'], name='seller_pts_tx_src_idx'),
                ],
            },
        ),
    ]
