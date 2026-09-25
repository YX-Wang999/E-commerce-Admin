"""Department tree utilities."""

from typing import Any


def build_department_tree(
    departments: list[dict[str, Any]],
    parent_id: int | None = None,
) -> list[dict[str, Any]]:
    """Build nested department tree from flat list."""
    tree: list[dict[str, Any]] = []
    for item in departments:
        if item.get('parent') == parent_id:
            children = build_department_tree(departments, item['id'])
            node = {key: value for key, value in item.items() if key != 'parent'}
            if children:
                node['children'] = children
            tree.append(node)
    return tree
