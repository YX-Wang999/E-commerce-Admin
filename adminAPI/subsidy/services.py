"""Subsidy calculation and query helpers."""

from __future__ import annotations

from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone

from subsidy.models import SubsidyOrder, SubsidyPolicy, SubsidyProduct


def _policy_in_window(policy: SubsidyPolicy, now=None) -> bool:
    now = now or timezone.now()
    if policy.start_time and policy.start_time > now:
        return False
    if policy.end_time and policy.end_time < now:
        return False
    return True


def get_active_policy(region: str = '', category: str = '') -> SubsidyPolicy | None:
    """Return the latest active policy within its time window."""
    now = timezone.now()
    qs = SubsidyPolicy.objects.filter(is_active=True)
    if region:
        qs = qs.filter(Q(region='') | Q(region=region))
    if category:
        qs = qs.filter(Q(category='') | Q(category=category))
    for policy in qs.order_by('-updated_at'):
        if _policy_in_window(policy, now):
            return policy
    return None


def calculate_subsidy_amount(price: Decimal, policy: SubsidyPolicy) -> Decimal:
    """Calculate subsidy amount for a given price and policy."""
    price = Decimal(price or 0)
    if price <= 0:
        return Decimal('0')

    if policy.subsidy_type == SubsidyPolicy.TYPE_PERCENT:
        amount = (price * Decimal(policy.subsidy_value) / Decimal('100')).quantize(Decimal('0.01'))
        if policy.max_subsidy is not None:
            amount = min(amount, Decimal(policy.max_subsidy))
    else:
        amount = Decimal(policy.subsidy_value)

    return min(amount, price).quantize(Decimal('0.01'))


def apply_filing_approved(row: SubsidyProduct) -> None:
    """Recalculate subsidy amount when government filing is approved."""
    row.subsidy_amount = calculate_subsidy_amount(row.product.price, row.policy)
    row.save(update_fields=['subsidy_amount', 'updated_at'])


def build_subsidy_payload(*, product, policy: SubsidyPolicy, subsidy_amount: Decimal) -> dict:
    price = Decimal(product.price or 0)
    subsidy = Decimal(subsidy_amount or 0)
    final_price = max(price - subsidy, Decimal('0')).quantize(Decimal('0.01'))
    formula = (
        f'原价 ¥{price} × {policy.subsidy_value}%'
        if policy.subsidy_type == SubsidyPolicy.TYPE_PERCENT
        else f'固定补贴 ¥{policy.subsidy_value}'
    )
    if policy.max_subsidy and policy.subsidy_type == SubsidyPolicy.TYPE_PERCENT:
        formula += f'（最高 ¥{policy.max_subsidy}）'

    return {
        'is_subsidy': True,
        'policy_id': policy.id,
        'policy_name': policy.name,
        'policy_description': policy.description,
        'subsidy_type': policy.subsidy_type,
        'subsidy_value': str(policy.subsidy_value),
        'max_subsidy': str(policy.max_subsidy) if policy.max_subsidy is not None else None,
        'original_price': str(price),
        'subsidy_amount': str(subsidy),
        'final_price': str(final_price),
        'formula': formula,
        'government_subsidy': True,
    }


def get_approved_subsidy_for_product(product_id: int) -> dict | None:
    """Return subsidy info for a government-approved filing, or None."""
    row = (
        SubsidyProduct.objects.filter(
            product_id=product_id,
            filing_status=SubsidyProduct.FILING_APPROVED,
            policy__is_active=True,
        )
        .select_related('product', 'policy')
        .first()
    )
    if not row or not _policy_in_window(row.policy):
        return None
    return build_subsidy_payload(
        product=row.product,
        policy=row.policy,
        subsidy_amount=row.subsidy_amount,
    )


def calculate_for_product(product_id: int, quantity: int = 1) -> dict | None:
    info = get_approved_subsidy_for_product(product_id)
    if not info:
        return None
    qty = max(int(quantity or 1), 1)
    unit_subsidy = Decimal(info['subsidy_amount'])
    unit_final = Decimal(info['final_price'])
    return {
        **info,
        'quantity': qty,
        'total_subsidy': str((unit_subsidy * qty).quantize(Decimal('0.01'))),
        'total_final_price': str((unit_final * qty).quantize(Decimal('0.01'))),
    }


def check_subsidy_eligibility(*, product_id: int, customer=None, region: str = '') -> dict:
    """Check whether a customer can purchase a subsidy product."""
    row = (
        SubsidyProduct.objects.filter(product_id=product_id)
        .select_related('product', 'policy')
        .first()
    )
    product = row.product if row else None
    policy_active = bool(row and row.policy.is_active and _policy_in_window(row.policy))

    checks = {
        'product_exists': product is not None and product.is_active,
        'product_filed': row is not None and row.filing_status == SubsidyProduct.FILING_APPROVED,
        'policy_active': policy_active,
        'region_available': True if not region else (not row or not row.region or row.region == region),
        'identity_verified': bool(
            customer
            and getattr(customer, 'real_name', None)
            and getattr(customer, 'id_card', None),
        ),
    }
    eligible = all(checks.values())
    messages = []
    if not checks['product_filed']:
        messages.append('商品尚未完成政府备案')
    if not checks['policy_active']:
        messages.append('当前地区暂无国补活动')
    if not checks['identity_verified']:
        messages.append('请先完成实名认证')
    if not checks['region_available']:
        messages.append('该地区暂不支持国补')

    return {
        'eligible': eligible,
        'checks': checks,
        'messages': messages,
        'subsidy': calculate_for_product(product_id) if eligible else None,
    }


def subsidy_stats() -> dict:
    approved = SubsidyProduct.objects.filter(filing_status=SubsidyProduct.FILING_APPROVED)
    aggregates = approved.aggregate(
        total_subsidy=Sum('subsidy_amount'),
        product_count=Count('id'),
        merchant_count=Count('tenant_id', distinct=True),
    )
    order_qs = SubsidyOrder.objects.all()
    order_stats = order_qs.aggregate(
        order_count=Count('id'),
        pending_report=Count('id', filter=Q(government_status=SubsidyOrder.GOV_PENDING)),
        reported=Count('id', filter=Q(government_status=SubsidyOrder.GOV_REPORTED)),
        verified=Count('id', filter=Q(government_status=SubsidyOrder.GOV_VERIFIED)),
        failed=Count('id', filter=Q(government_status=SubsidyOrder.GOV_FAILED)),
    )
    return {
        'total_subsidy_amount': str(aggregates['total_subsidy'] or 0),
        'approved_product_count': aggregates['product_count'] or 0,
        'merchant_count': aggregates['merchant_count'] or 0,
        'submitted_count': SubsidyProduct.objects.filter(
            filing_status=SubsidyProduct.FILING_SUBMITTED,
        ).count(),
        'rejected_count': SubsidyProduct.objects.filter(
            filing_status=SubsidyProduct.FILING_REJECTED,
        ).count(),
        'order_count': order_stats['order_count'] or 0,
        'order_pending_report': order_stats['pending_report'] or 0,
        'order_reported': order_stats['reported'] or 0,
        'order_verified': order_stats['verified'] or 0,
        'order_failed': order_stats['failed'] or 0,
    }


def seller_available_products_queryset(tenant, policy: SubsidyPolicy | None = None):
    """On-sale products without active filing in progress or approved."""
    from products.models import Product

    blocked = SubsidyProduct.objects.filter(
        tenant=tenant,
        filing_status__in=[
            SubsidyProduct.FILING_SUBMITTED,
            SubsidyProduct.FILING_APPROVED,
        ],
    ).values_list('product_id', flat=True)
    return Product.all_objects.filter(
        tenant=tenant,
        is_active=True,
        status=Product.STATUS_ON_SALE,
    ).exclude(id__in=blocked)


def build_filing_export_payload(row: SubsidyProduct) -> dict:
    """Generate government filing material checklist for a product."""
    product = row.product
    return {
        'product_id': product.id,
        'product_name': product.name,
        'product_price': str(product.price),
        'tenant_name': row.tenant.name if row.tenant_id else '',
        'region': row.region,
        'category': row.category,
        'policy_name': row.policy.name,
        'filing_status': row.filing_status,
        'filing_status_label': row.get_filing_status_display(),
        'materials': [
            '营业执照副本',
            '商品销售授权书',
            '商品质检报告',
            'SN/IMEI 备案信息',
            '政府补贴申报表（加盖公章）',
        ],
        'guide_url': 'https://www.mofcom.gov.cn/',
    }
