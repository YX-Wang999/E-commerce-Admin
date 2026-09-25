from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0007_customer_diamond_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='real_name',
            field=models.CharField(blank=True, default='', max_length=64, verbose_name='真实姓名'),
        ),
    ]
