"""Move tenant menus to top-level 商户管理 directory."""

from django.db import migrations


def restructure_tenant_menus(apps, schema_editor):
    from accounts.rbac_seed import seed_default_roles_migration
    from tenants.tenant_seed import seed_tenant_directory_menu

    menu_model = apps.get_model('rbac', 'Menu')
    permission_model = apps.get_model('rbac', 'Permission')
    permissions = {
        item.code: item
        for item in permission_model.objects.filter(code__startswith='tenant:')
    }
    seed_tenant_directory_menu(menu_model, permissions)

    chat = menu_model.objects.filter(name='ChatWorkbench').first()
    if chat:
        chat.title = '商城客服'
        chat.save(update_fields=['title'])

    seed_default_roles_migration(apps, schema_editor)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0004_tenant_suspension_appeal'),
    ]

    operations = [
        migrations.RunPython(restructure_tenant_menus, noop),
    ]
