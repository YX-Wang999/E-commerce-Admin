"""Set existing users to not require first-login password change."""

from django.db import migrations


def set_existing_users_not_first_login(apps, schema_editor) -> None:
    """Mark all existing users as having completed first login."""
    user_model = apps.get_model('accounts', 'User')
    user_model.objects.update(is_first_login=False)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_add_user_is_first_login'),
    ]

    operations = [
        migrations.RunPython(
            set_existing_users_not_first_login,
            migrations.RunPython.noop,
        ),
    ]
