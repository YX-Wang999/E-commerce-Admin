# Generated manually

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customers', '0001_initial'),
        ('orders', '0001_initial'),
        ('reviews', '0001_initial'),
        ('tenants', '0009_tenant_description'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ShopRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('overall_score', models.DecimalField(decimal_places=1, default=5.0, max_digits=3, verbose_name='综合评分')),
                ('quality_score', models.DecimalField(decimal_places=1, default=5.0, max_digits=3, verbose_name='商品质量')),
                ('service_score', models.DecimalField(decimal_places=1, default=5.0, max_digits=3, verbose_name='服务态度')),
                ('logistics_score', models.DecimalField(decimal_places=1, default=5.0, max_digits=3, verbose_name='物流速度')),
                ('total_ratings', models.PositiveIntegerField(default=0, verbose_name='评价总数')),
                ('total_orders', models.PositiveIntegerField(default=0, verbose_name='总订单数')),
                ('completed_orders', models.PositiveIntegerField(default=0, verbose_name='已完成订单')),
                ('refund_orders', models.PositiveIntegerField(default=0, verbose_name='退款订单')),
                ('initial_score', models.DecimalField(decimal_places=1, default=5.0, max_digits=3, verbose_name='初始评分')),
                ('initial_weight_threshold', models.PositiveIntegerField(default=10, verbose_name='初始分衰减阈值')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('tenant', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='shop_rating', to='tenants.tenant', verbose_name='商家')),
            ],
            options={
                'verbose_name': '店铺评分',
                'verbose_name_plural': '店铺评分',
                'db_table': 'shop_rating_shop_rating',
            },
        ),
        migrations.CreateModel(
            name='UserRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quality_score', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='商品质量评分')),
                ('service_score', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='服务态度评分')),
                ('logistics_score', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='物流速度评分')),
                ('content', models.TextField(blank=True, default='', verbose_name='评价内容')),
                ('images', models.JSONField(blank=True, default=list, verbose_name='评价图片')),
                ('is_anonymous', models.BooleanField(default=False, verbose_name='是否匿名')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shop_ratings', to='customers.customer', verbose_name='会员')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='shop_ratings', to='orders.order', verbose_name='关联订单')),
                ('product_review', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='shop_user_rating', to='reviews.productreview', verbose_name='商品评价')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_ratings', to='tenants.tenant', verbose_name='商家')),
            ],
            options={
                'verbose_name': '用户评价',
                'verbose_name_plural': '用户评价',
                'db_table': 'shop_rating_user_rating',
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='RatingScoreHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('overall_score', models.DecimalField(decimal_places=1, max_digits=3, verbose_name='综合评分')),
                ('recorded_at', models.DateTimeField(auto_now_add=True, verbose_name='记录时间')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rating_history', to='tenants.tenant', verbose_name='商家')),
            ],
            options={
                'verbose_name': '评分历史',
                'verbose_name_plural': '评分历史',
                'db_table': 'shop_rating_score_history',
                'ordering': ['-recorded_at'],
            },
        ),
        migrations.CreateModel(
            name='RatingAdjustmentRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('current_score', models.DecimalField(decimal_places=1, max_digits=3, verbose_name='当前评分')),
                ('requested_score', models.DecimalField(decimal_places=1, max_digits=3, verbose_name='申请评分')),
                ('reason', models.CharField(max_length=200, verbose_name='申请理由')),
                ('status', models.CharField(choices=[('pending', '待审核'), ('approved', '已通过'), ('rejected', '已驳回')], default='pending', max_length=20, verbose_name='状态')),
                ('review_note', models.CharField(blank=True, default='', max_length=200, verbose_name='审核备注')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='申请时间')),
                ('reviewed_at', models.DateTimeField(blank=True, null=True, verbose_name='审核时间')),
                ('reviewer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_rating_requests', to=settings.AUTH_USER_MODEL, verbose_name='审核人')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rating_adjustment_requests', to='tenants.tenant', verbose_name='商家')),
            ],
            options={
                'verbose_name': '评分调整申请',
                'verbose_name_plural': '评分调整申请',
                'db_table': 'shop_rating_adjustment_request',
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='RatingAdjustmentLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_score', models.DecimalField(decimal_places=1, max_digits=3, verbose_name='原评分')),
                ('new_score', models.DecimalField(decimal_places=1, max_digits=3, verbose_name='新评分')),
                ('reason', models.CharField(max_length=200, verbose_name='调整原因')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('operator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='shop_rating_adjustments', to=settings.AUTH_USER_MODEL, verbose_name='操作人')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rating_logs', to='tenants.tenant', verbose_name='商家')),
            ],
            options={
                'verbose_name': '评分调整日志',
                'verbose_name_plural': '评分调整日志',
                'db_table': 'shop_rating_adjustment_log',
                'ordering': ['-id'],
            },
        ),
    ]
