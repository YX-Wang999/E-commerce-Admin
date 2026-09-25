from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0006_rename_customers_s_phone_s_6f8d0d_idx_customers_s_phone_75dbe1_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='level',
            field=models.CharField(
                choices=[
                    ('normal', '普通会员'),
                    ('silver', '白银会员'),
                    ('gold', '黄金会员'),
                    ('platinum', '铂金会员'),
                    ('diamond', '钻石会员'),
                ],
                default='normal',
                max_length=16,
                verbose_name='会员等级',
            ),
        ),
    ]
