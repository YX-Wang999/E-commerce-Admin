# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0003_customer_phone_e164'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsverificationcode',
            name='out_id',
            field=models.CharField(blank=True, default='', max_length=64, verbose_name='阿里云OutId'),
        ),
        migrations.AlterField(
            model_name='smsverificationcode',
            name='phone',
            field=models.CharField(max_length=32, verbose_name='手机号'),
        ),
    ]
