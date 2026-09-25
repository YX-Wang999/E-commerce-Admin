# Generated manually for brand logo fields

from django.db import migrations, models


class Migration(migrations.Migration):
    """Split brand logo into ImageField and logo_url."""

    dependencies = [
        ('products', '0003_inventorylog'),
    ]

    operations = [
        migrations.RenameField(
            model_name='brand',
            old_name='logo',
            new_name='logo_url',
        ),
        migrations.AlterField(
            model_name='brand',
            name='logo_url',
            field=models.URLField(
                blank=True,
                max_length=500,
                null=True,
                verbose_name='Logo 链接',
            ),
        ),
        migrations.AddField(
            model_name='brand',
            name='logo',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='brands/%Y/%m/',
                verbose_name='Logo 文件',
            ),
        ),
    ]
