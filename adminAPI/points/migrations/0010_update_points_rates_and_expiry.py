"""Update points rates and backfill account expiry."""

from datetime import timedelta
from decimal import Decimal

from django.db import migrations
from django.utils import timezone


def forwards(apps, schema_editor):
    PointsRule = apps.get_model('points', 'PointsRule')
    PointsAccount = apps.get_model('points', 'PointsAccount')

    PointsRule.objects.filter(code='order_rate').update(
        current_value=Decimal('0.1'),
        default_value=Decimal('0.1'),
        description='每消费 10 元 = 1 积分',
    )
    PointsRule.objects.filter(code='redeem_rate').update(
        current_value=Decimal('10'),
        default_value=Decimal('10'),
        description='10 积分 = 1 元',
    )

    expire_at = timezone.now() + timedelta(days=365)
    PointsAccount.objects.filter(balance_expire_at__isnull=True).update(balance_expire_at=expire_at)


class Migration(migrations.Migration):

    dependencies = [
        ('points', '0009_pointsaccount_expire_at'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
