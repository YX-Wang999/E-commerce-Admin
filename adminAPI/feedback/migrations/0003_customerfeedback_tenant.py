# Generated manually — tenant-scoped customer feedback

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0002_feedback_menu_seed'),
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customerfeedback',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='feedbacks',
                to='tenants.tenant',
                verbose_name='关联商户',
            ),
        ),
    ]
