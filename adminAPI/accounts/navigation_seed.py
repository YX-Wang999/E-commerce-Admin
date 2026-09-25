"""Navigation v1.0 seed: report sub-menus and logistics."""

from typing import Any

REPORT_FINANCE_PERMISSION = ('财务汇总查看', 'report:finance', '数据报表', 'finance')

REPORT_MENU_DEFS: list[tuple] = [
    ('ReportSales', '销售报表', '/reports/sales', 'reports/SalesReportView', 'TrendCharts', 51, 'report:read'),
    ('ReportProductRank', '商品排行', '/reports/product-rank', 'reports/ProductRankView', 'Medal', 52, 'report:read'),
    ('ReportCustomer', '客户分析', '/reports/customer', 'reports/CustomerAnalysisView', 'User', 53, 'report:read'),
    ('ReportPromotion', '促销分析', '/reports/promotion', 'reports/PromotionAnalysisView', 'Ticket', 54, 'report:read'),
    ('ReportFinance', '财务汇总', '/reports/finance', 'reports/FinanceReportView', 'Coin', 55, 'report:finance'),
]

LOGISTICS_MENU_DEF = (
    'LogisticsList',
    '物流管理',
    '/orders/logistics',
    'orders/LogisticsList',
    'Van',
    33,
    'order:ship',
)


def seed_report_finance_permission(permission_model: Any) -> dict[str, Any]:
    """Create finance report permission."""
    name, code, module, action = REPORT_FINANCE_PERMISSION
    permission, _ = permission_model.objects.update_or_create(
        code=code,
        defaults={
            'name': name,
            'module': module,
            'action': action,
            'description': name,
        },
    )
    return {code: permission}


def seed_navigation_menus(
    menu_model: Any,
    report_dir: Any,
    order_dir: Any,
    permissions: dict[str, Any],
) -> dict[str, Any]:
    """Create report sub-menus and logistics menu."""
    menus: dict[str, Any] = {}
    menu_model.objects.filter(name='ReportView').delete()
    for name, title, path, component, icon, sort_order, perm_code in REPORT_MENU_DEFS:
        menu, _ = menu_model.objects.update_or_create(
            name=name,
            defaults={
                'title': title,
                'path': path,
                'component': component,
                'icon': icon,
                'menu_type': 'menu',
                'sort_order': sort_order,
                'parent': report_dir,
                'permission': permissions.get(perm_code),
                'is_visible': True,
                'is_active': True,
            },
        )
        menus[name] = menu
    lname, ltitle, lpath, lcomp, licon, lsort, lperm = LOGISTICS_MENU_DEF
    logistics, _ = menu_model.objects.update_or_create(
        name=lname,
        defaults={
            'title': ltitle,
            'path': lpath,
            'component': lcomp,
            'icon': licon,
            'menu_type': 'menu',
            'sort_order': lsort,
            'parent': order_dir,
            'permission': permissions.get(lperm),
            'is_visible': True,
            'is_active': True,
        },
    )
    menus[lname] = logistics
    return menus


def seed_navigation_v1_migration(apps, schema_editor) -> None:
    """Migration hook: expand navigation and refresh roles."""
    from accounts.rbac_seed import seed_default_roles_migration

    permission_model = apps.get_model('rbac', 'Permission')
    menu_model = apps.get_model('rbac', 'Menu')
    permissions = {item.code: item for item in permission_model.objects.all()}
    permissions.update(seed_report_finance_permission(permission_model))
    report_dir = menu_model.objects.filter(name='ReportDir').first()
    order_dir = menu_model.objects.filter(name='OrderDir').first()
    if report_dir and order_dir:
        seed_navigation_menus(menu_model, report_dir, order_dir, permissions)
    seed_default_roles_migration(apps, schema_editor)
