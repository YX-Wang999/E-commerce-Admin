"""Seed default promotional tags."""

from django.db import migrations


def forwards_seed_tags(apps, schema_editor):
    from tag_system.services import seed_default_tags

    seed_default_tags()


class Migration(migrations.Migration):

    dependencies = [
        ('tag_system', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards_seed_tags, migrations.RunPython.noop),
    ]
