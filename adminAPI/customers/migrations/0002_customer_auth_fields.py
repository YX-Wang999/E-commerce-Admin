"""Customer auth fields and SMS verification."""

import django.contrib.auth.hashers
from django.db import migrations, models


def set_default_passwords(apps, schema_editor):
    Customer = apps.get_model('customers', 'Customer')
    for customer in Customer.objects.filter(password=''):
        customer.password = django.contrib.auth.hashers.make_password('changeme123')
        if not customer.nickname:
            customer.nickname = customer.name
        customer.save(update_fields=['password', 'nickname'])


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='nickname',
            field=models.CharField(blank=True, default='', max_length=64, verbose_name='昵称'),
        ),
        migrations.AddField(
            model_name='customer',
            name='avatar',
            field=models.URLField(blank=True, default='', max_length=512, verbose_name='头像'),
        ),
        migrations.AddField(
            model_name='customer',
            name='password',
            field=models.CharField(default='', max_length=128, verbose_name='密码'),
            preserve_default=False,
        ),
        migrations.RunPython(set_default_passwords, migrations.RunPython.noop),
        migrations.CreateModel(
            name='SmsVerificationCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(max_length=20, verbose_name='手机号')),
                ('code', models.CharField(max_length=8, verbose_name='验证码')),
                ('scene', models.CharField(choices=[('register', '注册'), ('reset_password', '找回密码')], max_length=32, verbose_name='场景')),
                ('expires_at', models.DateTimeField(verbose_name='过期时间')),
                ('is_used', models.BooleanField(default=False, verbose_name='是否已使用')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
            ],
            options={
                'verbose_name': '短信验证码',
                'verbose_name_plural': '短信验证码',
                'db_table': 'customers_sms_code',
                'ordering': ['-id'],
            },
        ),
        migrations.AddIndex(
            model_name='smsverificationcode',
            index=models.Index(fields=['phone', 'scene', '-created_at'], name='customers_s_phone_s_6f8d0d_idx'),
        ),
        migrations.AlterModelOptions(
            name='customer',
            options={'ordering': ['-id'], 'verbose_name': '商城用户', 'verbose_name_plural': '商城用户'},
        ),
    ]
