"""Add unique contact_phone and normalize duplicate values."""

from django.db import migrations, models


def dedupe_contact_phones(apps, schema_editor):
    Tenant = apps.get_model('tenants', 'Tenant')
    seen = {}
    for tenant in Tenant.objects.order_by('id'):
        phone = (tenant.contact_phone or '').strip()
        if not phone:
            tenant.contact_phone = f'pending_{tenant.id}'
            tenant.save(update_fields=['contact_phone'])
            phone = tenant.contact_phone
        if phone in seen:
            suffix = 1
            new_phone = f'{phone}_{suffix}'
            while Tenant.objects.filter(contact_phone=new_phone).exists():
                suffix += 1
                new_phone = f'{phone}_{suffix}'
            tenant.contact_phone = new_phone
            tenant.save(update_fields=['contact_phone'])
            phone = new_phone
        seen[phone] = tenant.id


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0002_tenant_department_actionlog'),
    ]

    operations = [
        migrations.RunPython(dedupe_contact_phones, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='tenant',
            name='contact_phone',
            field=models.CharField(max_length=20, unique=True, verbose_name='联系电话'),
        ),
    ]
