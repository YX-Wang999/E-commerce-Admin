"""Category tree helpers."""

from django.core.cache import cache

from products.models import Category

MAX_CATEGORY_DEPTH = 5
CACHE_KEY_TREE = 'products:category_tree'
CACHE_TIMEOUT = 300


def invalidate_category_cache() -> None:
    """Clear cached category tree."""
    cache.delete(CACHE_KEY_TREE)
    cache.delete(f'{CACHE_KEY_TREE}:active')
    cache.delete(f'{CACHE_KEY_TREE}:all')


def get_category_level(category: Category) -> int:
    """Return 1-based depth of a category."""
    level = 1
    parent_id = category.parent_id
    visited: set[int] = set()
    while parent_id:
        if parent_id in visited:
            break
        visited.add(parent_id)
        level += 1
        if level > MAX_CATEGORY_DEPTH:
            break
        parent_id = Category.objects.filter(pk=parent_id).values_list('parent_id', flat=True).first()
    return level


def get_category_full_path(category: Category) -> str:
    """Return breadcrumb path like '电子产品 > 电脑整机'."""
    names: list[str] = []
    node_id = category.id
    node_name = category.name
    names.append(node_name)
    parent_id = category.parent_id
    visited: set[int] = {node_id}
    while parent_id:
        if parent_id in visited:
            break
        visited.add(parent_id)
        row = Category.objects.filter(pk=parent_id).values_list('name', 'parent_id').first()
        if not row:
            break
        names.insert(0, row[0])
        parent_id = row[1]
    return ' > '.join(names)


def get_all_descendant_ids(category: Category, *, active_only: bool = False) -> list[int]:
    """Return descendant category ids (excluding self)."""
    ids: list[int] = []
    children = category.children.all()
    if active_only:
        children = children.filter(is_active=True)
    for child in children:
        ids.append(child.id)
        ids.extend(get_all_descendant_ids(child, active_only=active_only))
    return ids


def get_category_children_ids(category: Category, *, active_only: bool = True) -> list[int]:
    """Return category id and all descendant ids."""
    ids = [category.id]
    children = category.children.all()
    if active_only:
        children = children.filter(is_active=True)
    for child in children:
        ids.extend(get_category_children_ids(child, active_only=active_only))
    return ids


def is_descendant(ancestor_id: int, category_id: int) -> bool:
    """Check whether category_id is under ancestor_id."""
    if ancestor_id == category_id:
        return True
    try:
        category = Category.objects.get(pk=category_id)
    except Category.DoesNotExist:
        return False
    node = category
    visited: set[int] = set()
    while node.parent_id:
        if node.parent_id in visited:
            return False
        visited.add(node.parent_id)
        if node.parent_id == ancestor_id:
            return True
        node = Category.objects.filter(pk=node.parent_id).only('id', 'parent_id').first()
        if node is None:
            break
    return False


def validate_parent_assignment(category: Category | None, parent: Category | None) -> str | None:
    """Validate parent move/create. Return error message or None."""
    if parent is None:
        return None
    if category and parent.id == category.id:
        return '不能将自己设为父级分类'
    if category and is_descendant(category.id, parent.id):
        return '不能将子分类设为父级分类'
    parent_level = get_category_level(parent)
    if parent_level >= MAX_CATEGORY_DEPTH:
        return f'分类层级不能超过 {MAX_CATEGORY_DEPTH} 层'
    if category:
        subtree_depth = _max_subtree_depth(category)
        if parent_level + subtree_depth > MAX_CATEGORY_DEPTH:
            return f'移动后分类层级将超过 {MAX_CATEGORY_DEPTH} 层'
    elif parent_level + 1 > MAX_CATEGORY_DEPTH:
        return f'分类层级不能超过 {MAX_CATEGORY_DEPTH} 层'
    return None


def _max_subtree_depth(category: Category) -> int:
    """Max depth of subtree rooted at category (including self = 1)."""
    children = list(category.children.all())
    if not children:
        return 1
    return 1 + max(_max_subtree_depth(child) for child in children)


def count_products_in_subtree(category: Category) -> int:
    """Count products assigned to category or any descendant."""
    from products.models import Product

    ids = get_category_children_ids(category, active_only=False)
    return Product.objects.filter(category_id__in=ids).count()


def count_children(category: Category) -> int:
    """Count direct child categories."""
    return category.children.count()
