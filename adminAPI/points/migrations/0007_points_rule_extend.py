# Generated migration for extended points rules

from decimal import Decimal

from django.db import migrations, models


def forwards_migrate_rule_values(apps, schema_editor):
    PointsRule = apps.get_model('points', 'PointsRule')
    for row in PointsRule.objects.all():
        legacy = Decimal(str(row.points_value or 0))
        row.default_value = legacy
        row.current_value = legacy
        row.description = row.description or ''
        if row.code in ('redeem_rate', 'redeem_max_rate', 'redeem_min_amount'):
            row.rule_type = 'redeem'
            row.is_system = True
        else:
            row.rule_type = 'earn'
            row.is_system = True
        row.save(update_fields=[
            'default_value', 'current_value', 'description', 'rule_type', 'is_system', 'points_value',
        ])


class Migration(migrations.Migration):

    dependencies = [
        ('points', '0006_points_refund_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='pointsrule',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='创建时间'),
        ),
        migrations.AlterField(
            model_name='pointsrule',
            name='code',
            field=models.CharField(max_length=50, unique=True, verbose_name='规则编码'),
        ),
        migrations.AlterField(
            model_name='pointsrule',
            name='name',
            field=models.CharField(max_length=100, verbose_name='规则名称'),
        ),
        migrations.AlterField(
            model_name='pointsrule',
            name='description',
            field=models.TextField(blank=True, default='', verbose_name='说明'),
        ),
        migrations.AddField(
            model_name='pointsrule',
            name='rule_type',
            field=models.CharField(
                choices=[('earn', '赚取积分'), ('redeem', '消耗积分')],
                default='earn',
                max_length=20,
                verbose_name='规则类型',
            ),
        ),
        migrations.AddField(
            model_name='pointsrule',
            name='default_value',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='默认值'),
        ),
        migrations.AddField(
            model_name='pointsrule',
            name='current_value',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='当前值'),
        ),
        migrations.AddField(
            model_name='pointsrule',
            name='min_value',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='最小值'),
        ),
        migrations.AddField(
            model_name='pointsrule',
            name='max_value',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='最大值'),
        ),
        migrations.AddField(
            model_name='pointsrule',
            name='is_system',
            field=models.BooleanField(default=False, verbose_name='系统内置'),
        ),
        migrations.AddField(
            model_name='pointsrule',
            name='trigger_config',
            field=models.JSONField(blank=True, default=dict, verbose_name='触发配置'),
        ),
        migrations.AddField(
            model_name='pointsrule',
            name='sort_order',
            field=models.IntegerField(default=0, verbose_name='排序'),
        ),
        migrations.RunPython(forwards_migrate_rule_values, migrations.RunPython.noop),
    ]
