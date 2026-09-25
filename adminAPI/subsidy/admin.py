from django.contrib import admin

from subsidy.models import SubsidyOrder, SubsidyPolicy, SubsidyProduct


@admin.register(SubsidyPolicy)
class SubsidyPolicyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'region', 'category', 'subsidy_type', 'subsidy_value', 'is_active', 'updated_at')


@admin.register(SubsidyProduct)
class SubsidyProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'tenant', 'filing_status', 'region', 'subsidy_amount', 'updated_at')
    list_filter = ('filing_status',)


@admin.register(SubsidyOrder)
class SubsidyOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'tenant', 'government_status', 'reported_at')
    list_filter = ('government_status',)
