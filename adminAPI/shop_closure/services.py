"""Shop closure business logic."""

from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from chat.models import Complaint
from orders.models import Order, Refund
from products.models import Product
from shop_closure.models import ClosureApplication, ClosureChecklist, ClosureNotification
from tenants.models import Tenant, TenantInboxMessage, TenantStaff

logger = logging.getLogger(__name__)
User = get_user_model()

OPEN_ORDER_STATUSES = [
    Order.STATUS_PENDING,
    Order.STATUS_PAID,
    Order.STATUS_SHIPPED,
    Order.STATUS_REFUNDING,
]
UNRESOLVED_COMPLAINT_STATUSES = [
    Complaint.STATUS_PENDING,
    Complaint.STATUS_MERCHANT_PROCESSING,
    Complaint.STATUS_CUSTOMER_REVIEW,
    Complaint.STATUS_PLATFORM_REVIEWING,
    Complaint.STATUS_REVIEWING,
]

CHECK_DEFINITIONS = [
    ('open_orders', '未完成订单'),
    ('pending_refunds', '未处理售后'),
    ('unsettled_balance', '未提现资金'),
    ('deposit', '保证金'),
    ('complaints', '未处理投诉'),
]


def _tenant_config(tenant: Tenant) -> dict:
    return tenant.config if isinstance(tenant.config, dict) else {}


def evaluate_closure_conditions(tenant: Tenant) -> list[dict]:
    """Return checklist evaluation for a tenant."""
    order_qs = Order.all_objects.filter(tenant=tenant)
    open_orders = order_qs.filter(status__in=OPEN_ORDER_STATUSES).count()
    pending_refunds = Refund.objects.filter(
        order__tenant=tenant,
        status=Refund.STATUS_PENDING,
    ).count()
    config = _tenant_config(tenant)
    unsettled_balance = Decimal(str(config.get('unsettled_balance', 0) or 0))
    deposit_settled = bool(config.get('deposit_settled', True))
    open_complaints = Complaint.objects.filter(
        tenant=tenant,
        status__in=UNRESOLVED_COMPLAINT_STATUSES,
    ).count()

    checks = [
        {
            'code': 'open_orders',
            'item': '未完成订单',
            'is_completed': open_orders == 0,
            'remark': '' if open_orders == 0 else f'您有 {open_orders} 笔订单未完成，请先处理',
            'count': open_orders,
        },
        {
            'code': 'pending_refunds',
            'item': '未处理售后',
            'is_completed': pending_refunds == 0,
            'remark': '' if pending_refunds == 0 else f'您有 {pending_refunds} 笔售后未处理',
            'count': pending_refunds,
        },
        {
            'code': 'unsettled_balance',
            'item': '未提现资金',
            'is_completed': unsettled_balance <= 0,
            'remark': '' if unsettled_balance <= 0 else f'您有 ¥{unsettled_balance:.2f} 未提现，请先提现',
            'count': float(unsettled_balance),
        },
        {
            'code': 'deposit',
            'item': '保证金',
            'is_completed': deposit_settled,
            'remark': '' if deposit_settled else '保证金未结算，请联系平台',
            'count': 0 if deposit_settled else 1,
        },
        {
            'code': 'complaints',
            'item': '未处理投诉',
            'is_completed': open_complaints == 0,
            'remark': '' if open_complaints == 0 else f'您有 {open_complaints} 笔投诉未处理',
            'count': open_complaints,
        },
    ]
    return checks


def conditions_met(tenant: Tenant) -> tuple[bool, list[dict]]:
    checks = evaluate_closure_conditions(tenant)
    return all(item['is_completed'] for item in checks), checks


def get_active_closure_application(tenant: Tenant) -> ClosureApplication | None:
    return (
        ClosureApplication.objects.filter(
            tenant=tenant,
            status__in=[
                ClosureApplication.STATUS_PENDING,
                ClosureApplication.STATUS_APPROVED,
                ClosureApplication.STATUS_NOTICE_PERIOD,
            ],
        )
        .order_by('-id')
        .first()
    )


def tenant_closure_state(tenant: Tenant) -> dict:
    app = (
        ClosureApplication.objects.filter(tenant=tenant)
        .order_by('-id')
        .first()
    )
    if tenant.status == Tenant.STATUS_CLOSED:
        return {'state': 'closed', 'notice_end_at': None, 'application_id': app.id if app else None}
    if app and app.status == ClosureApplication.STATUS_NOTICE_PERIOD:
        return {
            'state': 'closing',
            'notice_end_at': app.notice_end_at.isoformat() if app.notice_end_at else None,
            'application_id': app.id,
        }
    return {'state': 'active', 'notice_end_at': None, 'application_id': app.id if app else None}


def _sync_checklist(application: ClosureApplication, checks: list[dict]) -> None:
    now = timezone.now()
    for row in checks:
        ClosureChecklist.objects.update_or_create(
            application=application,
            code=row['code'],
            defaults={
                'item': row['item'],
                'is_completed': row['is_completed'],
                'completed_at': now if row['is_completed'] else None,
                'remark': row.get('remark') or '',
            },
        )


def _notify_customers(application: ClosureApplication, *, closing: bool) -> None:
    from customers.models import Customer

    since = timezone.now() - timedelta(days=180)
    customer_ids = (
        Order.all_objects.filter(tenant=application.tenant, created_at__gte=since)
        .values_list('customer_id', flat=True)
        .distinct()
    )
    tenant_name = application.tenant.name
    if closing:
        end_text = application.notice_end_at.strftime('%Y-%m-%d') if application.notice_end_at else '近期'
        content = f'店铺「{tenant_name}」将于 {end_text} 关闭，请留意未完成订单与售后。'
    else:
        content = f'店铺「{tenant_name}」已正式关闭，感谢您的支持。'

    for customer_id in customer_ids:
        customer = Customer.all_objects.filter(pk=customer_id).first()
        if customer is None:
            continue
        ClosureNotification.objects.create(
            application=application,
            recipient=customer.phone or customer.name,
            channel=ClosureNotification.CHANNEL_IN_APP,
            content=content,
            is_delivered=True,
        )


def _mark_closure_approval(application: ClosureApplication, reviewer: User, *, approved: bool) -> None:
    from approval.models import Approval
    from approval.services import mark_approval_finished

    approval = Approval.objects.filter(
        business_type='shop_closure.application',
        business_id=application.id,
        status=Approval.STATUS_PENDING,
    ).first()
    if approval is None:
        return
    mark_approval_finished(
        approval,
        status=Approval.STATUS_APPROVED if approved else Approval.STATUS_REJECTED,
        reviewer=reviewer,
        reject_reason='' if approved else application.reject_reason,
        notify_applicant=False,
    )


@transaction.atomic
def create_closure_application(tenant: Tenant, *, reason: str, detail: str = '', attachments: list | None = None) -> ClosureApplication:
    if tenant.status == Tenant.STATUS_CLOSED:
        raise ValueError('店铺已注销')
    if tenant.status == Tenant.STATUS_PENDING:
        raise ValueError('待审核店铺无法申请注销')
    if get_active_closure_application(tenant):
        raise ValueError('已有进行中的注销申请')

    ok, checks = conditions_met(tenant)
    if not ok:
        failed = [item['remark'] for item in checks if not item['is_completed'] and item['remark']]
        raise ValueError('；'.join(failed[:3]) or '注销条件未满足')

    application = ClosureApplication.objects.create(
        tenant=tenant,
        reason=reason.strip(),
        detail=(detail or '').strip(),
        attachments=attachments or [],
        status=ClosureApplication.STATUS_PENDING,
    )
    _sync_checklist(application, checks)
    TenantInboxMessage.objects.create(
        tenant=tenant,
        message_type=TenantInboxMessage.TYPE_SYSTEM,
        title='店铺注销申请已提交',
        content='您的注销申请已进入平台审核，请耐心等待。',
    )
    from approval.services import sync_closure_approval

    sync_closure_approval(application)
    return application


@transaction.atomic
def approve_closure_application(application: ClosureApplication, reviewer: User, *, notice_days: int | None = None) -> ClosureApplication:
    if application.status != ClosureApplication.STATUS_PENDING:
        raise ValueError('当前状态不可审核通过')
    ok, checks = conditions_met(application.tenant)
    if not ok:
        raise ValueError('注销条件未满足，无法通过审核')
    days = notice_days or application.notice_days or 15
    now = timezone.now()
    application.status = ClosureApplication.STATUS_NOTICE_PERIOD
    application.reviewed_by = reviewer
    application.reviewed_at = now
    application.notice_days = days
    application.notice_start_at = now
    application.notice_end_at = now + timedelta(days=days)
    application.save(
        update_fields=[
            'status',
            'reviewed_by',
            'reviewed_at',
            'notice_days',
            'notice_start_at',
            'notice_end_at',
            'updated_at',
        ],
    )
    _sync_checklist(application, checks)
    _notify_customers(application, closing=True)
    TenantInboxMessage.objects.create(
        tenant=application.tenant,
        message_type=TenantInboxMessage.TYPE_SYSTEM,
        title='注销申请已通过，进入公示期',
        content=f'公示期 {days} 天，请于 {application.notice_end_at:%Y-%m-%d} 前处理剩余事务。',
    )
    _mark_closure_approval(application, reviewer, approved=True)
    return application


@transaction.atomic
def reject_closure_application(application: ClosureApplication, reviewer: User, *, reject_reason: str) -> ClosureApplication:
    if application.status != ClosureApplication.STATUS_PENDING:
        raise ValueError('当前状态不可驳回')
    application.status = ClosureApplication.STATUS_REJECTED
    application.reviewed_by = reviewer
    application.reviewed_at = timezone.now()
    application.reject_reason = reject_reason.strip()
    application.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'reject_reason', 'updated_at'])
    TenantInboxMessage.objects.create(
        tenant=application.tenant,
        message_type=TenantInboxMessage.TYPE_SYSTEM,
        title='注销申请被驳回',
        content=application.reject_reason or '请完善条件后重新申请。',
    )
    _mark_closure_approval(application, reviewer, approved=False)
    return application


@transaction.atomic
def cancel_closure_application(application: ClosureApplication) -> ClosureApplication:
    if application.status not in {
        ClosureApplication.STATUS_PENDING,
        ClosureApplication.STATUS_NOTICE_PERIOD,
    }:
        raise ValueError('当前状态不可撤回')
    application.status = ClosureApplication.STATUS_CANCELLED
    application.save(update_fields=['status', 'updated_at'])
    return application


@transaction.atomic
def execute_closure(application: ClosureApplication, *, operator: User | None = None) -> ClosureApplication:
    if application.status != ClosureApplication.STATUS_NOTICE_PERIOD:
        raise ValueError('仅公示期满的申请可执行注销')
    if application.notice_end_at and application.notice_end_at > timezone.now():
        raise ValueError('公示期尚未结束')
    ok, checks = conditions_met(application.tenant)
    if not ok:
        raise ValueError('注销条件未满足，无法完成注销')

    tenant = application.tenant
    Product.all_objects.filter(tenant=tenant, is_active=True).update(is_active=False)
    tenant.status = Tenant.STATUS_CLOSED
    tenant.is_active = False
    tenant.save(update_fields=['status', 'is_active', 'updated_at'])

    staff_user_ids = TenantStaff.objects.filter(tenant=tenant).values_list('user_id', flat=True)
    User.objects.filter(id__in=staff_user_ids).update(is_active=False)

    now = timezone.now()
    application.status = ClosureApplication.STATUS_COMPLETED
    application.completed_at = now
    application.reviewed_by = application.reviewed_by or operator
    application.save(update_fields=['status', 'completed_at', 'reviewed_by', 'updated_at'])
    _sync_checklist(application, checks)
    _notify_customers(application, closing=False)

    logger.info('Shop closure completed tenant=%s application=%s', tenant.id, application.id)
    return application


def process_due_closures() -> int:
    """Complete closure applications whose notice period has ended."""
    now = timezone.now()
    queryset = ClosureApplication.objects.filter(
        status=ClosureApplication.STATUS_NOTICE_PERIOD,
        notice_end_at__lte=now,
    )
    completed = 0
    for application in queryset:
        try:
            execute_closure(application)
            completed += 1
        except ValueError as exc:
            logger.warning('Skip auto closure application=%s: %s', application.id, exc)
    return completed
