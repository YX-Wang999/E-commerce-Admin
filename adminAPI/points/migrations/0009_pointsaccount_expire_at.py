from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('points', '0008_alter_pointsrule_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='pointsaccount',
            name='balance_expire_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='积分过期时间'),
        ),
    ]
