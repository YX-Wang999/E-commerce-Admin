# Fix PointsRule.created_at: backfill nulls then enforce non-null

from django.db import migrations, models
from django.utils import timezone


def backfill_points_rule_created_at(apps, schema_editor):
    PointsRule = apps.get_model('points', 'PointsRule')
    now = timezone.now()
    PointsRule.objects.filter(created_at__isnull=True).update(created_at=now)


class Migration(migrations.Migration):

    dependencies = [
        ('points', '0007_points_rule_extend'),
    ]

    operations = [
        migrations.RunPython(backfill_points_rule_created_at, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='pointsrule',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='创建时间'),
        ),
        migrations.AlterModelOptions(
            name='pointsrule',
            options={
                'ordering': ['rule_type', 'sort_order', 'id'],
                'verbose_name': '积分规则',
                'verbose_name_plural': '积分规则',
            },
        ),
        migrations.AlterField(
            model_name='pointsrule',
            name='points_value',
            field=models.PositiveIntegerField(default=0, verbose_name='积分值(旧)'),
        ),
    ]
