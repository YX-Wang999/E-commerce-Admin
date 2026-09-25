"""Approval sync hooks."""

from __future__ import annotations


def backfill_pending_approvals() -> dict[str, int]:
    """Import existing pending business records into the approval workbench."""
    from approval.services import sync_closure_approval, sync_subsidy_approval, sync_tag_approval
    from shop_closure.models import ClosureApplication
    from subsidy.models import SubsidyProduct
    from tag_system.models import TenantTagConfig

    counts = {'closure': 0, 'tag': 0, 'subsidy': 0}
    for application in ClosureApplication.objects.filter(status=ClosureApplication.STATUS_PENDING).select_related('tenant'):
        sync_closure_approval(application)
        counts['closure'] += 1
    for config in TenantTagConfig.objects.filter(status=TenantTagConfig.STATUS_PENDING).select_related('tenant', 'tag'):
        sync_tag_approval(config)
        counts['tag'] += 1
    for row in SubsidyProduct.objects.filter(
        filing_status=SubsidyProduct.FILING_SUBMITTED,
    ).select_related('product', 'tenant'):
        sync_subsidy_approval(row)
        counts['subsidy'] += 1
    return counts
