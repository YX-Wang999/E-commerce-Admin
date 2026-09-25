"""Announcement permission helpers."""

from rest_framework.permissions import BasePermission

from feedback.permissions import user_has_permission


class HasAnnouncementRead(BasePermission):
    """Read announcement management list."""

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'announcement:read')


class HasAnnouncementCreate(BasePermission):
    """Create announcements."""

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'announcement:create')


class HasAnnouncementUpdate(BasePermission):
    """Update announcements."""

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'announcement:update')


class HasAnnouncementDelete(BasePermission):
    """Delete announcements."""

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'announcement:delete')


class HasAnnouncementPublish(BasePermission):
    """Publish or offline announcements."""

    def has_permission(self, request, view) -> bool:
        return user_has_permission(request.user, 'announcement:publish')
