"""Data-scope helpers for users and audit logs."""

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

User = get_user_model()


def is_super_admin(user: User) -> bool:
    """Whether the user has full system access."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.roles.filter(code='super_admin', is_active=True).exists()


def is_dept_manager(user: User) -> bool:
    """Whether the user has the department manager role."""
    if not user or not user.is_authenticated:
        return False
    return user.roles.filter(code='dept_manager', is_active=True).exists()


def get_managed_department_ids(user: User) -> list[int]:
    """Department ids the user manages via Department.manager."""
    return list(
        user.managed_departments.filter(is_active=True).values_list('id', flat=True),
    )


def filter_users_by_scope(queryset: QuerySet, user: User) -> QuerySet:
    """Restrict user queryset by role data scope."""
    if is_super_admin(user):
        return queryset
    if is_dept_manager(user):
        dept_ids = get_managed_department_ids(user)
        if dept_ids:
            return queryset.filter(department_id__in=dept_ids)
        return queryset.filter(pk=user.pk)
    return queryset.filter(pk=user.pk)


def filter_audit_logs_by_scope(queryset: QuerySet, user: User) -> QuerySet:
    """Restrict audit log queryset by role data scope."""
    if is_super_admin(user):
        return queryset
    if is_dept_manager(user):
        dept_ids = get_managed_department_ids(user)
        if dept_ids:
            return queryset.filter(user__department_id__in=dept_ids)
        return queryset.filter(user=user)
    return queryset.filter(user=user)
