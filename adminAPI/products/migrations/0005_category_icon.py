# Generated manually for category icon field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_brand_logo_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='icon',
            field=models.CharField(blank=True, default='', max_length=64, verbose_name='分类图标'),
        ),
    ]
