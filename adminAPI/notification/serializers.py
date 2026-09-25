"""Notification API serializers."""

from rest_framework import serializers

from notification.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'content',
            'type',
            'related_url',
            'related_id',
            'need_popup',
            'need_sound',
            'is_read',
            'read_at',
            'created_at',
        ]
        read_only_fields = fields
