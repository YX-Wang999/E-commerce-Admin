from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('promotion', '0003_coupon_tenant_groupbuyactivity_tenant_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='usercoupon',
            name='customer',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='user_coupons',
                to='customers.customer',
                verbose_name='商城会员',
            ),
        ),
        migrations.AlterField(
            model_name='usercoupon',
            name='user',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='user_coupons',
                to=settings.AUTH_USER_MODEL,
                verbose_name='用户',
            ),
        ),
    ]
