"""Organization chart tree builders."""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model

from accounts.scopes import get_managed_department_ids, is_dept_manager, is_super_admin

User = get_user_model()

ORG_VIEW_ROLES = {'ops_director', 'ops_manager'}


def _primary_role_code(user: User) -> str | None:
    """Return the first active role code."""
    role = user.roles.filter(is_active=True).order_by('id').first()
    return role.code if role else None


def _display_name(user: User) -> str:
    """Human-readable name for org chart nodes."""
    return user.nickname or user.get_full_name() or user.username


def serialize_org_node(user: User) -> dict[str, Any]:
    """Serialize a user to org chart node dict."""
    role = user.roles.filter(is_active=True).order_by('id').first()
    return {
        'id': user.id,
        'username': user.username,
        'display_name': _display_name(user),
        'role': role.code if role else None,
        'role_name': role.name if role else None,
        'department': user.department.name if user.department_id else None,
        'avatar': user.avatar or None,
    }


def _load_active_users() -> tuple[dict[int, User], dict[int | None, list[int]]]:
    """Load active users and supervisor → subordinates map."""
    users = list(
        User.objects.filter(is_active=True)
        .select_related('department', 'supervisor')
        .prefetch_related('roles')
        .order_by('id'),
    )
    users_by_id = {user.id: user for user in users}
    children_map: dict[int | None, list[int]] = {}
    for user in users:
        children_map.setdefault(user.supervisor_id, []).append(user.id)
    for child_ids in children_map.values():
        child_ids.sort()
    return users_by_id, children_map


def build_subtree(
    user_id: int,
    users_by_id: dict[int, User],
    children_map: dict[int | None, list[int]],
    allowed_ids: set[int] | None = None,
) -> dict[str, Any] | None:
    """Build nested org node including descendants."""
    if allowed_ids is not None and user_id not in allowed_ids:
        return None
    user = users_by_id.get(user_id)
    if user is None:
        return None
    node = serialize_org_node(user)
    child_nodes = []
    for child_id in children_map.get(user_id, []):
        child = build_subtree(child_id, users_by_id, children_map, allowed_ids)
        if child is not None:
            child_nodes.append(child)
    if child_nodes:
        node['children'] = child_nodes
    return node


def _find_root_within_allowed(
    user: User,
    allowed_ids: set[int],
    users_by_id: dict[int, User],
) -> User:
    """Walk up supervisors while the parent remains in the allowed set."""
    current = user
    while current.supervisor_id and current.supervisor_id in allowed_ids:
        current = users_by_id[current.supervisor_id]
    return current


def _trees_for_super_admin(
    users_by_id: dict[int, User],
    children_map: dict[int | None, list[int]],
) -> list[dict[str, Any]]:
    """Full company tree from top-level leaders."""
    root_ids = children_map.get(None, [])
    if not root_ids:
        return []
    return [
        tree
        for root_id in root_ids
        if (tree := build_subtree(root_id, users_by_id, children_map)) is not None
    ]


def _trees_for_dept_manager(
    user: User,
    users_by_id: dict[int, User],
    children_map: dict[int | None, list[int]],
) -> list[dict[str, Any]]:
    """Trees for departments the user manages."""
    managed_ids = get_managed_department_ids(user)
    if not managed_ids:
        tree = build_subtree(user.id, users_by_id, children_map)
        return [tree] if tree else []

    allowed_ids = {
        uid
        for uid, item in users_by_id.items()
        if item.department_id in managed_ids
    }
    if not allowed_ids:
        tree = build_subtree(user.id, users_by_id, children_map)
        return [tree] if tree else []

    roots: list[User] = []
    seen_root_ids: set[int] = set()
    for uid in allowed_ids:
        root = _find_root_within_allowed(users_by_id[uid], allowed_ids, users_by_id)
        if root.id not in seen_root_ids:
            seen_root_ids.add(root.id)
            roots.append(root)

    trees: list[dict[str, Any]] = []
    for root in sorted(roots, key=lambda item: item.id):
        tree = build_subtree(root.id, users_by_id, children_map, allowed_ids)
        if tree is not None:
            trees.append(tree)
    return trees


def _has_role_code(user: User, code: str) -> bool:
    """Check whether user has a role code using prefetched roles."""
    return any(role.code == code for role in user.roles.all())


def _trees_for_ops_leader(
    user: User,
    users_by_id: dict[int, User],
    children_map: dict[int | None, list[int]],
) -> list[dict[str, Any]]:
    """Ops director / manager view: department tree from ops director."""
    role_codes = set(user.roles.filter(is_active=True).values_list('code', flat=True))
    root = user
    if 'ops_manager' in role_codes and user.department_id:
        director = next(
            (
                item
                for item in users_by_id.values()
                if item.department_id == user.department_id
                and _has_role_code(item, 'ops_director')
            ),
            None,
        )
        if director is not None:
            root = director
    tree = build_subtree(root.id, users_by_id, children_map)
    return [tree] if tree else []


def get_org_tree(user: User) -> list[dict[str, Any]]:
    """Return org chart trees visible to the current user."""
    users_by_id, children_map = _load_active_users()

    if is_super_admin(user):
        return _trees_for_super_admin(users_by_id, children_map)

    if is_dept_manager(user):
        return _trees_for_dept_manager(user, users_by_id, children_map)

    role_codes = set(user.roles.filter(is_active=True).values_list('code', flat=True))
    if role_codes & ORG_VIEW_ROLES:
        return _trees_for_ops_leader(user, users_by_id, children_map)

    tree = build_subtree(user.id, users_by_id, children_map)
    return [tree] if tree else []
