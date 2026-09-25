"""Customer signals."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from customers.models import Customer


@receiver(post_save, sender=Customer)
def ensure_points_account_on_create(sender, instance, created, **kwargs):
    """Create points account when a mall customer registers."""
    if not created:
        return
    from points.models import PointsAccount

    PointsAccount.objects.get_or_create(
        customer=instance,
        tenant=instance.tenant,
        defaults={
            'balance': instance.points,
            'total_earned': instance.points,
            'total_spent': 0,
        },
    )
