"""Feedback menu, permissions and demo data seed."""

from typing import Any

FEEDBACK_PERMISSIONS: list[tuple[str, str, str, str]] = [
    ('留言查看', 'feedback:read', '客户留言', 'read'),
    ('留言回复', 'feedback:reply', '客户留言', 'reply'),
    ('留言删除', 'feedback:delete', '客户留言', 'delete'),
]

DEMO_FEEDBACKS: list[dict[str, Any]] = [
    {
        'nickname': '张先生',
        'phone': '13800001001',
        'feedback_type': 'complaint',
        'content': '订单发货太慢，希望加快物流速度。',
        'status': 'pending',
    },
    {
        'nickname': '李女士',
        'phone': '13800001002',
        'feedback_type': 'after_sales',
        'content': '收到的商品有轻微划痕，申请换货。',
        'status': 'processing',
    },
    {
        'nickname': '王先生',
        'phone': '13800001003',
        'feedback_type': 'suggestion',
        'content': '建议增加更多支付方式，如微信支付。',
        'status': 'done',
    },
    {
        'nickname': '赵小姐',
        'phone': '13800001004',
        'feedback_type': 'inquiry',
        'content': '请问会员积分如何兑换优惠券？',
        'status': 'pending',
    },
]


def seed_feedback_permissions(permission_model: Any) -> dict[str, Any]:
    """Create feedback permissions."""
    permissions: dict[str, Any] = {}
    for name, code, module, action in FEEDBACK_PERMISSIONS:
        permission, _ = permission_model.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'module': module,
                'action': action,
                'description': name,
            },
        )
        permissions[code] = permission
    return permissions


def seed_feedback_menu(menu_model: Any, customer_dir: Any, permissions: dict[str, Any]) -> Any:
    """Create customer feedback menu."""
    menu, _ = menu_model.objects.update_or_create(
        name='FeedbackList',
        defaults={
            'title': '客户留言',
            'path': '/customers/feedback',
            'component': 'customers/FeedbackList',
            'icon': 'ChatDotRound',
            'menu_type': 'menu',
            'sort_order': 42,
            'parent': customer_dir,
            'permission': permissions.get('feedback:read'),
            'is_visible': True,
            'is_active': True,
        },
    )
    return menu


def seed_demo_feedbacks(feedback_model: Any, customer_model: Any) -> None:
    """Seed demo feedback records."""
    for item in DEMO_FEEDBACKS:
        customer = customer_model.objects.filter(phone=item['phone']).first()
        feedback_model.objects.update_or_create(
            phone=item['phone'],
            content=item['content'],
            defaults={
                'customer': customer,
                'nickname': item['nickname'],
                'feedback_type': item['feedback_type'],
                'status': item['status'],
                'images': [],
            },
        )


def seed_feedback_migration(apps, schema_editor) -> None:
    """Migration hook: feedback menu, permissions, demo data."""
    from accounts.rbac_seed import seed_default_roles_migration

    permission_model = apps.get_model('rbac', 'Permission')
    menu_model = apps.get_model('rbac', 'Menu')
    feedback_model = apps.get_model('feedback', 'CustomerFeedback')
    customer_model = apps.get_model('customers', 'Customer')
    permissions = seed_feedback_permissions(permission_model)
    customer_dir = menu_model.objects.filter(name='CustomerDir').first()
    if customer_dir:
        seed_feedback_menu(menu_model, customer_dir, permissions)
    seed_demo_feedbacks(feedback_model, customer_model)
    seed_default_roles_migration(apps, schema_editor)
