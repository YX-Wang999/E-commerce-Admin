"""Merge parallel order migrations (receipt fields + seller points branch)."""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_order_receipt_fields'),
        ('orders', '0010_alter_cancellog_options_alter_cancellog_created_at_and_more'),
    ]

    operations = []
