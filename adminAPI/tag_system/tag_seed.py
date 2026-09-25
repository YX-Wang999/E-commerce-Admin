"""Seed default tags and admin menu."""

from typing import Any

from tag_system.services import seed_default_tags


def seed_tag_menus(menu_model: Any, system_dir: Any) -> None:
    if system_dir is None:
        system_dir = menu_model.objects.filter(name='System').first()
    if system_dir is None:
        return
    tag_dir, _ = menu_model.objects.update_or_create(
        name='TagSystemDir',
        defaults={
            'title': '标签管理',
            'path': '/system/tags',
            'icon': 'PriceTag',
            'menu_type': 'directory',
            'parent': system_dir,
            'sort_order': 45,
            'is_visible': True,
            'is_active': True,
        },
    )
    menu_model.objects.update_or_create(
        name='TagList',
        defaults={
            'title': '促销标签',
            'path': '/system/tags',
            'component': 'system/tags/TagListView',
            'icon': 'CollectionTag',
            'menu_type': 'menu',
            'parent': tag_dir,
            'sort_order': 1,
            'is_visible': True,
            'is_active': True,
        },
    )
    menu_model.objects.update_or_create(
        name='TagTenantReview',
        defaults={
            'title': '商家参与审核',
            'path': '/system/tag-reviews',
            'component': 'system/tags/TagReviewView',
            'icon': 'Checked',
            'menu_type': 'menu',
            'parent': tag_dir,
            'sort_order': 2,
            'is_visible': True,
            'is_active': True,
        },
    )


def seed_tags() -> None:
    seed_default_tags()
