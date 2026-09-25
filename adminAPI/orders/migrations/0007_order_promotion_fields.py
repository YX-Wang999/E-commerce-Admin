from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('promotion', '0003_coupon_tenant_groupbuyactivity_tenant_and_more'),
        ('orders', '0006_order_tenant'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='original_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='商品原价合计'),
        ),
        migrations.AddField(
            model_name='order',
            name='coupon_discount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='优惠券抵扣'),
        ),
        migrations.AddField(
            model_name='order',
            name='points_discount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='积分抵扣'),
        ),
        migrations.AddField(
            model_name='order',
            name='points_used',
            field=models.PositiveIntegerField(default=0, verbose_name='使用积分'),
        ),
        migrations.AddField(
            model_name='order',
            name='user_coupon',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='orders',
                to='promotion.usercoupon',
                verbose_name='使用优惠券',
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='promotion_type',
            field=models.CharField(blank=True, default='', max_length=16, verbose_name='促销类型'),
        ),
        migrations.AddField(
            model_name='order',
            name='promotion_ref',
            field=models.CharField(blank=True, default='', max_length=64, verbose_name='促销关联'),
        ),
    ]
