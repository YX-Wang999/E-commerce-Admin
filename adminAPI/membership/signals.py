"""Membership signals."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from customers.models import Customer
from membership.services import get_default_level, get_or_create_profile


@receiver(post_save, sender=Customer)
def ensure_member_profile_on_create(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        get_or_create_profile(instance)
    except Exception:
        # levels may not be seeded yet during migrations
        default_level = None
        try:
            default_level = get_default_level()
        except Exception:
            return
        from membership.models import MemberProfile

        MemberProfile.objects.get_or_create(
            customer=instance,
            defaults={'current_level': default_level, 'growth_points': 0},
        )
