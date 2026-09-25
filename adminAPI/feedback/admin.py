from django.contrib import admin

from feedback.models import CustomerFeedback


@admin.register(CustomerFeedback)
class CustomerFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'nickname', 'phone', 'feedback_type', 'status', 'created_at')
    list_filter = ('feedback_type', 'status')
    search_fields = ('nickname', 'phone', 'content')
