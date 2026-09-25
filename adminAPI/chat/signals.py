"""Chat model signals."""

from django.db.models.signals import pre_save
from django.dispatch import receiver

from chat.models import Message
from chat.utils import MessagePrivacy


@receiver(pre_save, sender=Message)
def auto_desensitize_message(sender, instance, **kwargs):
    """Mark sensitive content and store desensitized text only."""
    if not instance.content:
        instance.is_sensitive = False
        return
    instance.is_sensitive = MessagePrivacy.is_sensitive(instance.content)
    instance.content = MessagePrivacy.desensitize(instance.content)
