"""Points expiry reminder and auto-deduction."""

from __future__ import annotations

import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import DateField
from django.db.models.functions import Cast
from django.utils import timezone

from points.models import PointsAccount, PointsTransaction

logger = logging.getLogger(__name__)

REMIND_DAYS = (30, 7, 1)


def _remind_dedup_url(account_id: int, days_left: int) -> str:
    return f'/points?expire_remind={days_left}&account={account_id}'


def _already_reminded_today(*, customer_id: int, account_id: int, days_left: int) -> bool:
    from notification.models import Notification

    today = timezone.localdate()
    return Notification.objects.filter(
        recipient_type=Notification.RECIPIENT_CUSTOMER,
        recipient_id=customer_id,
        type=Notification.TYPE_POINTS,
        related_url=_remind_dedup_url(account_id, days_left),
        created_at__date=today,
    ).exists()


def _notify_reminder(account: PointsAccount, days_left: int) -> None:
    from notification.services import notify_points_expiry_reminder

    notify_points_expiry_reminder(
        customer_id=account.customer_id,
        account_id=account.id,
        balance=account.balance,
        days_left=days_left,
    )


def _notify_expired(customer_id: int, amount: int) -> None:
    from notification.services import notify_points_expired

    notify_points_expired(customer_id=customer_id, amount=amount)


def _accounts_expiring_in_days(days: int):
    target_date = timezone.localdate() + timedelta(days=days)
    return (
        PointsAccount.objects.filter(balance__gt=0, balance_expire_at__isnull=False)
        .annotate(expire_date=Cast('balance_expire_at', DateField()))
        .filter(expire_date=target_date)
        .select_related('customer')
    )


@transaction.atomic
def expire_account_points(account: PointsAccount) -> PointsTransaction | None:
    account = PointsAccount.objects.select_for_update().select_related('customer').get(pk=account.pk)
    if account.balance <= 0:
        return None
    if account.balance_expire_at is None or account.balance_expire_at >= timezone.now():
        return None

    amount = account.balance
    customer = account.customer
    source = f'points_expire:{account.id}:{timezone.localdate().isoformat()}'
    if PointsTransaction.objects.filter(customer=customer, source=source).exists():
        return None

    account.balance = 0
    account.total_spent += amount
    account.balance_expire_at = None
    account.save(update_fields=['balance', 'total_spent', 'balance_expire_at', 'updated_at'])

    txn = PointsTransaction.objects.create(
        customer=customer,
        amount=-amount,
        balance_after=0,
        trans_type=PointsTransaction.TYPE_SPEND_EXPIRE,
        source=source,
        description=f'积分过期扣除 {amount} 分',
    )

    if account.tenant_id is None:
        customer.points = 0
        customer.save(update_fields=['points', 'updated_at'])
    else:
        platform = PointsAccount.objects.filter(customer=customer, tenant__isnull=True).first()
        if platform:
            customer.points = platform.balance
            customer.save(update_fields=['points', 'updated_at'])

    try:
        _notify_expired(customer.id, amount)
    except Exception:
        logger.exception('Failed to notify points expiry for customer %s', customer.id)

    return txn


def check_and_notify_expiry() -> dict[str, int]:
    """Send 30/7/1-day expiry reminders."""
    counts = {f'remind_{days}': 0 for days in REMIND_DAYS}
    for days in REMIND_DAYS:
        for account in _accounts_expiring_in_days(days):
            if _already_reminded_today(
                customer_id=account.customer_id,
                account_id=account.id,
                days_left=days,
            ):
                continue
            try:
                _notify_reminder(account, days)
                counts[f'remind_{days}'] += 1
            except Exception:
                logger.exception(
                    'Failed to send %s-day expiry reminder for account %s',
                    days,
                    account.id,
                )
    return counts


def expire_points() -> int:
    """Deduct expired points and record ledger entries."""
    expired_qs = (
        PointsAccount.objects.filter(
            balance__gt=0,
            balance_expire_at__isnull=False,
            balance_expire_at__lt=timezone.now(),
        )
        .select_related('customer')
        .order_by('id')
    )
    count = 0
    for account in expired_qs:
        if expire_account_points(account):
            count += 1
    return count


def process_points_expiry() -> dict[str, int]:
    """Run reminder checks and expired-point deduction."""
    result = check_and_notify_expiry()
    result['expired'] = expire_points()
    return result
