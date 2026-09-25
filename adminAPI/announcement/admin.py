"""Django admin for announcements."""

from django.contrib import admin

from announcement.models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'announce_type', 'priority', 'status', 'published_at')
    list_filter = ('status', 'priority', 'announce_type')
    search_fields = ('title',)
