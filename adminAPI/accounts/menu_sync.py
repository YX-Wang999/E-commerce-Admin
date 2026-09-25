"""Sync sidebar menus and role assignments after deploy."""

from typing import Any

from accounts.rbac_seed import seed_default_roles
from rbac.models import Menu, Permission, Role


def _sync_permissions() -> dict[str, Any]:
    """Ensure baseline permission codes exist."""
    from accounts.ecommerce_seed import create_ecommerce_permissions
    from membership.membership_seed import seed_membership_permissions
    from tenants.tenant_seed import seed_tenant_permissions

    permissions: dict[str, Any] = {item.code: item for item in Permission.objects.all()}
    permissions.update(create_ecommerce_permissions())
    permissions.update(seed_tenant_permissions(Permission))
    permissions.update(seed_membership_permissions(Permission))
    return permissions


def sync_all_menus(*, refresh_roles: bool = True) -> dict[str, int]:
    """Upsert all platform sidebar menus and optionally refresh role menu bindings."""
    from accounts.ecommerce_seed import create_ecommerce_menus
    from approval.approval_seed import seed_approval_menus
    from complaints.complaint_seed import seed_complaint_menus
    from membership.membership_seed import seed_membership_menus
    from points.models import PointsRule
    from points.points_seed import seed_points_menus, seed_points_permissions, seed_points_rules
    from shop_closure.closure_seed import seed_closure_menus
    from shop_rating.shop_rating_seed import seed_shop_rating_menus, seed_shop_rating_permissions
    from subsidy.subsidy_seed import seed_subsidy_menus, seed_subsidy_permissions
    from tag_system.tag_seed import seed_tag_menus
    from tenants.tenant_seed import seed_tenant_directory_menu

    permissions = _sync_permissions()
    permissions.update(seed_points_permissions(Permission))
    permissions.update(seed_subsidy_permissions(Permission))
    permissions.update(seed_shop_rating_permissions(Permission))
    permissions = seed_complaint_menus(Menu, permissions, permission_model=Permission)

    # Core ecommerce tree (products, promotions incl. SuperDiscountList, orders, customers, reports, system)
    create_ecommerce_menus(permissions)
    seed_membership_menus(Menu, permissions)
    seed_tenant_directory_menu(Menu, permissions)

    # Incremental / module menus
    seed_approval_menus(Menu, permissions)
    seed_subsidy_menus(Menu, permissions)

    system_dir = Menu.objects.filter(name='System').first()
    seed_points_menus(Menu, system_dir, permissions)
    from points_mall.seed import seed_points_mall_menus

    seed_points_mall_menus(Menu, permissions)
    seed_tag_menus(Menu, system_dir)
    seed_closure_menus(Menu, system_dir, permissions)
    seed_points_rules(PointsRule)
    from points_mall.seed import seed_points_mall_items

    seed_points_mall_items()

    tenant_dir = Menu.objects.filter(name='TenantDir').first()
    seed_shop_rating_menus(Menu, permissions, tenant_dir=tenant_dir)

    from tag_system.services import seed_default_tags

    seed_default_tags()

    from approval.sync import backfill_pending_approvals

    backfill_pending_approvals()

    permissions = {item.code: item for item in Permission.objects.all()}
    role_count = 0
    if refresh_roles:
        menus = {item.name: item for item in Menu.objects.all()}
        seed_default_roles(permissions, menus, Role)
        role_count = Role.objects.count()

    return {
        'menu_count': Menu.objects.count(),
        'role_count': role_count,
    }
