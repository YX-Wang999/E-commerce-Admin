# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customers', '0001_initial'),
        ('promotion', '0001_initial'),
        ('points', '0009_pointsaccount_expire_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='PointsMallItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, verbose_name='商品名称')),
                ('image', models.CharField(blank=True, default='', max_length=500, verbose_name='图片')),
                ('description', models.TextField(blank=True, default='', verbose_name='描述')),
                ('item_type', models.CharField(choices=[('physical', '实物'), ('coupon', '优惠券'), ('benefit', '权益'), ('lottery', '抽奖')], db_index=True, default='physical', max_length=16)),
                ('points_required', models.PositiveIntegerField(verbose_name='所需积分')),
                ('stock', models.PositiveIntegerField(default=0, verbose_name='库存')),
                ('exchanged_count', models.PositiveIntegerField(default=0, verbose_name='已兑换数')),
                ('per_user_limit', models.PositiveIntegerField(default=1, verbose_name='每人限购')),
                ('requires_address', models.BooleanField(default=False, verbose_name='需要收货地址')),
                ('is_hot', models.BooleanField(default=False, verbose_name='热销')),
                ('is_limited_time', models.BooleanField(default=False, verbose_name='限时')),
                ('start_at', models.DateTimeField(blank=True, null=True, verbose_name='开始时间')),
                ('end_at', models.DateTimeField(blank=True, null=True, verbose_name='结束时间')),
                ('status', models.CharField(choices=[('draft', '草稿'), ('on_sale', '上架'), ('off_sale', '下架')], db_index=True, default='draft', max_length=16)),
                ('sort_order', models.IntegerField(default=0, verbose_name='排序')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('coupon_template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='points_mall_items', to='promotion.coupon', verbose_name='关联优惠券')),
            ],
            options={
                'verbose_name': '积分商品',
                'verbose_name_plural': '积分商品',
                'db_table': 'points_mall_item',
                'ordering': ['sort_order', '-id'],
            },
        ),
        migrations.CreateModel(
            name='PointsMallOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_no', models.CharField(max_length=32, unique=True, verbose_name='兑换单号')),
                ('item_name', models.CharField(max_length=120, verbose_name='商品名称快照')),
                ('item_type', models.CharField(max_length=16, verbose_name='商品类型快照')),
                ('points_spent', models.PositiveIntegerField(verbose_name='消耗积分')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='数量')),
                ('address', models.JSONField(blank=True, default=dict, verbose_name='收货地址')),
                ('status', models.CharField(choices=[('pending', '待处理'), ('processing', '处理中'), ('shipped', '已发货'), ('completed', '已完成'), ('cancelled', '已取消')], db_index=True, default='pending', max_length=16)),
                ('logistics_company', models.CharField(blank=True, default='', max_length=64, verbose_name='物流公司')),
                ('logistics_no', models.CharField(blank=True, default='', max_length=64, verbose_name='物流单号')),
                ('coupon_code', models.CharField(blank=True, default='', max_length=64, verbose_name='券码')),
                ('remark', models.CharField(blank=True, default='', max_length=255, verbose_name='备注')),
                ('shipped_at', models.DateTimeField(blank=True, null=True, verbose_name='发货时间')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='points_mall_orders', to='customers.customer', verbose_name='会员')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='points_mall.pointsmallitem', verbose_name='商品')),
            ],
            options={
                'verbose_name': '积分兑换订单',
                'verbose_name_plural': '积分兑换订单',
                'db_table': 'points_mall_order',
                'ordering': ['-id'],
            },
        ),
    ]
