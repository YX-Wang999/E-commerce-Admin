"""Tenant admin."""

from django.contrib import admin

from tenants.models import Tenant, TenantActionLog, TenantStaff


class TenantStaffInline(admin.TabularInline):
    model = TenantStaff
    extra = 0


class TenantActionLogInline(admin.TabularInline):
    model = TenantActionLog
    extra = 0
    readonly_fields = ('action', 'operator', 'remark', 'created_at')


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'status', 'department', 'is_active', 'contact_name', 'created_at')
    list_filter = ('status', 'is_active')
    search_fields = ('name', 'code', 'contact_name', 'contact_phone')
    inlines = [TenantStaffInline, TenantActionLogInline]


@admin.register(TenantStaff)
class TenantStaffAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'user', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')


@admin.register(TenantActionLog)
class TenantActionLogAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'action', 'operator', 'created_at')
    list_filter = ('action',)
