# Generated manually

from django.db import migrations


def seed_complaint_rbac(apps, schema_editor):
    from complaints.complaint_seed import seed_complaint_menu, seed_complaint_permissions

    permission_model = apps.get_model('rbac', 'Permission')
    menu_model = apps.get_model('rbac', 'Menu')
    role_model = apps.get_model('rbac', 'Role')
    permissions = seed_complaint_permissions(permission_model)
    customer_dir = menu_model.objects.filter(name='CustomerDir').first()
    if customer_dir:
        seed_complaint_menu(menu_model, customer_dir, permissions)
    for code in ['super_admin', 'cs_manager', 'cs_staff']:
        role = role_model.objects.filter(code=code).first()
        if role:
            for perm in permissions.values():
                role.permissions.add(perm)


class Migration(migrations.Migration):

    dependencies = [
        ('complaints', '0001_initial'),
        ('rbac', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_complaint_rbac, migrations.RunPython.noop),
    ]
