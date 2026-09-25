"""Announcement visibility helpers."""

from django.db.models import Case, IntegerField, Q, QuerySet, Value, When
from django.utils import timezone

from announcement.models import Announcement


def filter_visible_announcements(queryset: QuerySet, user) -> QuerySet:
    """Return published announcements visible to the given user."""
    now = timezone.now()
    queryset = queryset.filter(
        status=Announcement.STATUS_PUBLISHED,
        effective_at__lte=now,
        expires_at__gte=now,
    )

    roles = getattr(user, 'roles', None)
    if roles is None:
        return queryset.filter(scope=Announcement.SCOPE_ALL).distinct()

    role_ids = list(roles.filter(is_active=True).values_list('id', flat=True))
    dept_id = getattr(user, 'department_id', None)

    scope_filter = Q(scope=Announcement.SCOPE_ALL)
    if role_ids:
        scope_filter |= Q(scope=Announcement.SCOPE_ROLE, target_roles__id__in=role_ids)
    if dept_id:
        scope_filter |= Q(
            scope=Announcement.SCOPE_DEPARTMENT,
            target_departments__id=dept_id,
        )
    return queryset.filter(scope_filter).distinct()


def filter_banner_announcements(queryset: QuerySet, user) -> QuerySet:
    """Pinned or high-priority announcements for top banner."""
    return filter_visible_announcements(queryset, user).filter(
        Q(is_pinned=True)
        | Q(priority__in=[Announcement.PRIORITY_URGENT, Announcement.PRIORITY_IMPORTANT]),
    )


def order_banner_announcements(queryset: QuerySet) -> QuerySet:
    """Pinned first, then by priority and publish time."""
    priority_rank = Case(
        When(priority=Announcement.PRIORITY_URGENT, then=Value(3)),
        When(priority=Announcement.PRIORITY_IMPORTANT, then=Value(2)),
        default=Value(1),
        output_field=IntegerField(),
    )
    return queryset.annotate(_priority_rank=priority_rank).order_by(
        '-is_pinned',
        '-_priority_rank',
        '-published_at',
        '-id',
    )
