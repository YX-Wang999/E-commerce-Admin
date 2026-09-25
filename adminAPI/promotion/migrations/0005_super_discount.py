from decimal import Decimal

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def seed_default_super_discount(apps, schema_editor) -> None:
    SuperDiscount = apps.get_model('promotion', 'SuperDiscount')
    SuperDiscount.objects.update_or_create(
        title='超级立减',
        defaults={
            'promo_text': '全场好物立减',
            'amount': Decimal('15.00'),
            'button_text': '立即领取',
            'link_url': '/coupons',
            'is_active': True,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('promotion', '0004_usercoupon_customer'),
    ]

    operations = [
        migrations.CreateModel(
            name='SuperDiscount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='超级立减', max_length=64, verbose_name='活动标题')),
                ('promo_text', models.CharField(default='限时立减', max_length=128, verbose_name='宣传文案')),
                ('amount', models.DecimalField(decimal_places=2, default=15, max_digits=10, verbose_name='立减金额')),
                ('button_text', models.CharField(default='立即领取', max_length=32, verbose_name='按钮文案')),
                ('link_url', models.CharField(blank=True, default='', max_length=255, verbose_name='跳转链接')),
                ('is_active', models.BooleanField(default=True, verbose_name='启用')),
                ('start_time', models.DateTimeField(blank=True, null=True, verbose_name='开始时间')),
                ('end_time', models.DateTimeField(blank=True, null=True, verbose_name='结束时间')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_super_discounts', to=settings.AUTH_USER_MODEL, verbose_name='创建人')),
            ],
            options={
                'verbose_name': '超级立减',
                'verbose_name_plural': '超级立减',
                'db_table': 'promotion_super_discount',
                'ordering': ['-id'],
            },
        ),
        migrations.RunPython(seed_default_super_discount, migrations.RunPython.noop),
    ]
