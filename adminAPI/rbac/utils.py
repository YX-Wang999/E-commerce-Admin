"""Menu tree utilities and role-based menu filtering."""

from typing import Any

from django.contrib.auth import get_user_model

from rbac.models import Menu

User = get_user_model()

VISIBLE_MENU_TYPES = [Menu.MENU_TYPE_DIRECTORY, Menu.MENU_TYPE_MENU]
MENU_VALUE_FIELDS = (
    'id',
    'parent_id',
    'title',
    'name',
    'path',
    'component',
    'icon',
    'menu_type',
    'sort_order',
)


def build_menu_tree(
    menus: list[dict[str, Any]],
    parent_id: int | None = None,
) -> list[dict[str, Any]]:
    """Build nested menu tree from flat menu list."""
    tree: list[dict[str, Any]] = []
    for menu in menus:
        if menu.get('parent') == parent_id:
            children = build_menu_tree(menus, menu['id'])
            node = {key: value for key, value in menu.items() if key != 'parent'}
            if children:
                node['children'] = children
            tree.append(node)
    return tree


def _include_menu_ancestors(menu_ids: set[int]) -> set[int]:
    """Include parent directory menus required for tree rendering."""
    expanded = set(menu_ids)
    pending_ids = list(menu_ids)
    while pending_ids:
        parents = Menu.objects.filter(
            id__in=pending_ids,
            parent_id__isnull=False,
        ).values_list('parent_id', flat=True)
        new_ids = [parent_id for parent_id in parents if parent_id not in expanded]
        expanded.update(new_ids)
        pending_ids = new_ids
    return expanded


def _user_has_full_menu_access(user: User) -> bool:
    """Check whether user can access all menus."""
    if user.is_superuser:
        return True
    return user.roles.filter(code='super_admin', is_active=True).exists()


def _get_allowed_menu_ids(user: User) -> set[int]:
    """Get menu ids visible to the user based on roles."""
    base_qs = Menu.objects.filter(
        is_active=True,
        is_visible=True,
        menu_type__in=VISIBLE_MENU_TYPES,
    )
    if _user_has_full_menu_access(user):
        return set(base_qs.values_list('id', flat=True))
    role_menu_ids = set(
        base_qs.filter(
            roles__users=user,
            roles__is_active=True,
        ).values_list('id', flat=True).distinct(),
    )
    return _include_menu_ancestors(role_menu_ids)


def _normalize_menu_item(item: dict[str, Any]) -> dict[str, Any]:
    """Normalize menu queryset values to tree builder format."""
    return {
        'id': item['id'],
        'parent': item['parent_id'],
        'title': item['title'],
        'name': item['name'],
        'path': item['path'],
        'component': item['component'],
        'icon': item['icon'],
        'menu_type': item['menu_type'],
        'sort_order': item['sort_order'],
    }


def get_user_menu_tree(user: User) -> list[dict[str, Any]]:
    """Return role-filtered menu tree for the given user."""
    allowed_menu_ids = _get_allowed_menu_ids(user)
    if not allowed_menu_ids:
        return []
    flat_menus = list(
        Menu.objects.filter(id__in=allowed_menu_ids)
        .order_by('sort_order', 'id')
        .values(*MENU_VALUE_FIELDS),
    )
    normalized = [_normalize_menu_item(item) for item in flat_menus]
    return build_menu_tree(normalized)
