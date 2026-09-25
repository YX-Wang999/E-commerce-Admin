# Generated manually for login SMS scene

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0004_smsverificationcode_out_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='smsverificationcode',
            name='scene',
            field=models.CharField(
                choices=[
                    ('register', '注册'),
                    ('reset_password', '找回密码'),
                    ('login', '登录'),
                ],
                max_length=32,
                verbose_name='场景',
            ),
        ),
    ]
