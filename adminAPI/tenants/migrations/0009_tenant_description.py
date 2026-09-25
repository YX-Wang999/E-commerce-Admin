from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0008_tenant_business_license_tenant_legal_person_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tenant',
            name='description',
            field=models.TextField(blank=True, default='', verbose_name='店铺描述'),
        ),
    ]
