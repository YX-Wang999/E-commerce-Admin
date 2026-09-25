from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('points', '0004_rename_points_tran_custome_6f0d0d_idx_points_tran_custome_05059b_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pointstransaction',
            name='trans_type',
            field=models.CharField(
                choices=[
                    ('earn_sign_in', '签到奖励'),
                    ('earn_order', '订单奖励'),
                    ('earn_review', '评价奖励'),
                    ('spend_redeem', '积分兑换'),
                    ('spend_checkout', '下单抵扣'),
                    ('adjust_admin', '管理员调整'),
                ],
                max_length=32,
                verbose_name='类型',
            ),
        ),
    ]
