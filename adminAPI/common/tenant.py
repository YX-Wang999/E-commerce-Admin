"""Tenant-aware ORM managers and view mixins."""

from __future__ import annotations

from django.db import models

from tenants.context import get_current_tenant


class TenantAwareManager(models.Manager):
    """Automatically filter queryset by current tenant when set."""

    def get_queryset(self):
        queryset = super().get_queryset()
        tenant = get_current_tenant()
        if tenant is not None:
            return queryset.filter(tenant=tenant)
        return queryset


class TenantQuerySet(models.QuerySet):
    """QuerySet helpers for tenant scoping."""

    def for_tenant(self, tenant):
        if tenant is None:
            return self
        return self.filter(tenant=tenant)


class TenantViewSetMixin:
    """Filter viewset queryset by request tenant; platform superuser sees all."""

    tenant_field = 'tenant'

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self.request, 'customer', None) is not None:
            return queryset
        tenant = getattr(self.request, 'tenant', None)
        if tenant is not None:
            return queryset.filter(**{self.tenant_field: tenant})
        user = getattr(self.request, 'user', None)
        if user and getattr(user, 'is_authenticated', False) and getattr(user, 'is_superuser', False):
            return queryset
        if hasattr(user, 'roles'):
            return queryset
        return queryset.none()

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        if tenant is not None:
            serializer.save(tenant=tenant)
        else:
            serializer.save()
