from django.db import migrations


def seed_sensitive_words(apps, schema_editor):
    SystemSetting = apps.get_model('system', 'SystemSetting')
    SystemSetting.objects.update_or_create(
        key='tenant_name_sensitive_words',
        defaults={
            'value': '测试,admin,官方,平台,旗舰店',
            'value_type': 'string',
            'description': '商户名称敏感词（逗号分隔）',
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ('system', '0002_role_display_names_seed'),
    ]

    operations = [
        migrations.RunPython(seed_sensitive_words, migrations.RunPython.noop),
    ]
