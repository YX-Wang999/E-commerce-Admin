from django.db import migrations

from tenants.tenant_seed import seed_tenant_permissions, seed_tenant_directory_menu


def forwards(apps, schema_editor):
    permission_model = apps.get_model('rbac', 'Permission')
    menu_model = apps.get_model('rbac', 'Menu')
    role_model = apps.get_model('rbac', 'Role')
    permissions = seed_tenant_permissions(permission_model)
    seed_tenant_directory_menu(menu_model, permissions)
    for role_code, perm_codes in {
        'ops_director': [
            'tenant:view',
            'tenant:create',
            'tenant:approve',
            'tenant:suspend',
            'tenant:appeal',
            'tenant:change:view',
            'tenant:change:review',
        ],
        'ops_manager': ['tenant:view', 'tenant:change:view'],
    }.items():
        role = role_model.objects.filter(code=role_code).first()
        if role:
            role.permissions.add(*[permissions[c] for c in perm_codes if c in permissions])


class Migration(migrations.Migration):
    dependencies = [
        ('tenants', '0006_tenant_inbox_appeal_messages'),
        ('rbac', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
