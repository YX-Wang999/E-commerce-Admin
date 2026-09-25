from django.contrib import admin

from addresses.models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'name', 'phone', 'is_default', 'updated_at']
    list_filter = ['is_default']
