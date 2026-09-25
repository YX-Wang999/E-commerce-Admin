"""Add user supervisor self-reference."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add supervisor field to User."""

    dependencies = [
        ('accounts', '0014_department_menu_seed'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='supervisor',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='subordinates',
                to=settings.AUTH_USER_MODEL,
                verbose_name='直属上级',
            ),
        ),
    ]
