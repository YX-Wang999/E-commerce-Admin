"""Membership business logic."""

from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from customers.models import Customer
from membership.models import GrowthLog, MemberLevel, MemberProfile

logger = logging.getLogger(__name__)

LEVEL_LEGACY_MAP = {
    1: Customer.LEVEL_NORMAL,
    2: Customer.LEVEL_SILVER,
    3: Customer.LEVEL_GOLD,
    4: Customer.LEVEL_PLATINUM,
    5: 'diamond',
}


def get_default_level() -> MemberLevel:
    level = MemberLevel.objects.filter(is_active=True).order_by('level').first()
    if level is None:
        raise MemberLevel.DoesNotExist('请先初始化会员等级数据')
    return level


def get_or_create_profile(customer: Customer) -> MemberProfile:
    profile = (
        MemberProfile.objects.select_related('current_level')
        .filter(customer=customer)
        .first()
    )
    if profile:
        return profile
    default_level = get_default_level()
    profile, _ = MemberProfile.objects.get_or_create(
        customer=customer,
        defaults={
            'current_level': default_level,
            'growth_points': 0,
        },
    )
    _sync_customer_legacy_level(customer, profile.current_level)
    return profile


def _sync_customer_legacy_level(customer: Customer, level: MemberLevel) -> None:
    legacy = LEVEL_LEGACY_MAP.get(level.level, Customer.LEVEL_NORMAL)
    if customer.level != legacy:
        customer.level = legacy
        customer.save(update_fields=['level', 'updated_at'])


def _has_growth_source(customer: Customer, source: str) -> bool:
    if not source:
        return False
    return GrowthLog.objects.filter(customer=customer, source=source).exists()


@transaction.atomic
def add_growth_points(
    customer: Customer,
    amount: int,
    log_type: str,
    description: str = '',
    *,
    source: str = '',
) -> GrowthLog | None:
    if amount == 0:
        return None
    if source and _has_growth_source(customer, source):
        return None

    profile = get_or_create_profile(customer)
    profile = MemberProfile.objects.select_for_update().select_related('current_level').get(
        pk=profile.pk,
    )
    profile.growth_points = max(0, profile.growth_points + amount)
    profile.save(update_fields=['growth_points', 'updated_at'])

    log = GrowthLog.objects.create(
        customer=customer,
        amount=amount,
        balance_after=profile.growth_points,
        log_type=log_type,
        description=description,
        source=source,
    )
    check_level_upgrade(customer, profile=profile)
    return log


@transaction.atomic
def check_level_upgrade(customer: Customer, *, profile: MemberProfile | None = None) -> bool:
    if profile is None:
        profile = MemberProfile.objects.select_for_update().select_related('current_level').get(
            customer=customer,
        )
    else:
        profile = MemberProfile.objects.select_for_update().select_related('current_level').get(
            pk=profile.pk,
        )

    upgraded = False
    while True:
        next_level = (
            MemberLevel.objects.filter(
                min_points__lte=profile.growth_points,
                is_active=True,
                level__gt=profile.current_level.level,
            )
            .order_by('-level')
            .first()
        )
        if next_level is None or next_level.level <= profile.current_level.level:
            break

        profile.current_level = next_level
        profile.level_upgraded_at = timezone.now()
        profile.save(update_fields=['current_level', 'level_upgraded_at', 'updated_at'])
        _sync_customer_legacy_level(customer, next_level)

        GrowthLog.objects.create(
            customer=customer,
            amount=0,
            balance_after=profile.growth_points,
            log_type=GrowthLog.TYPE_LEVEL_UP,
            description=f'升级至 {next_level.name}',
            source=f'level_up:{next_level.level}:{profile.id}',
        )
        upgraded = True

    return upgraded


def calculate_order_points(customer: Customer, order_amount) -> int:
    """Reward points with membership multiplier."""
    profile = get_or_create_profile(customer)
    multiplier = profile.current_level.points_multiplier if profile.current_level else Decimal('1.00')
    base_points = int(Decimal(order_amount) // Decimal(10))
    return int(base_points * multiplier)


def award_order_growth(order) -> GrowthLog | None:
    if not order.customer_id:
        return None
    source = f'order_growth:{order.id}'
    points = int(Decimal(order.total_amount) // Decimal(10))
    if points <= 0:
        return None
    return add_growth_points(
        order.customer,
        points,
        GrowthLog.TYPE_ORDER,
        description=f'订单 {order.order_no} 消费奖励',
        source=source,
    )


@transaction.atomic
def checkin(customer: Customer) -> dict:
    profile = get_or_create_profile(customer)
    profile = MemberProfile.objects.select_for_update().get(pk=profile.pk)
    today = timezone.localdate()

    if profile.last_checkin_date == today:
        return {'code': 400, 'message': '今日已签到', 'profile': profile}

    if profile.last_checkin_date == today - timedelta(days=1):
        profile.checkin_streak += 1
    else:
        profile.checkin_streak = 1

    profile.total_checkins += 1
    profile.last_checkin_date = today
    profile.save(
        update_fields=[
            'checkin_streak',
            'total_checkins',
            'last_checkin_date',
            'updated_at',
        ],
    )

    streak_bonus = 0
    if profile.checkin_streak >= 7 and profile.checkin_streak % 7 == 0:
        streak_bonus = 5

    total_gain = 5 + streak_bonus
    source = f'checkin:{today.isoformat()}'
    add_growth_points(
        customer,
        total_gain,
        GrowthLog.TYPE_SIGN_IN,
        description='每日签到' + (f'，连续{profile.checkin_streak}天奖励' if streak_bonus else ''),
        source=source,
    )
    profile.refresh_from_db()

    message = '签到成功'
    if streak_bonus:
        message += f'，连续签到奖励 +{streak_bonus}'

    return {
        'code': 0,
        'message': message,
        'growth_points': total_gain,
        'checkin_streak': profile.checkin_streak,
        'profile': profile,
    }


def build_profile_payload(customer: Customer) -> dict:
    profile = get_or_create_profile(customer)
    profile = MemberProfile.objects.select_related('current_level').get(pk=profile.pk)
    today = timezone.localdate()
    checked_in_today = profile.last_checkin_date == today

    next_level = (
        MemberLevel.objects.filter(
            is_active=True,
            level__gt=profile.current_level.level,
        )
        .order_by('level')
        .first()
    )

    if next_level:
        progress_base = profile.current_level.min_points
        span = max(next_level.min_points - progress_base, 1)
        gained = profile.growth_points - progress_base
        progress_percent = min(100.0, round(gained / span * 100, 1))
        points_to_next = max(next_level.min_points - profile.growth_points, 0)
    else:
        progress_percent = 100.0
        points_to_next = 0
        next_level = None

    level = profile.current_level
    return {
        'current_level': {
            'level': level.level,
            'name': level.name,
            'min_points': level.min_points,
            'discount_rate': level.discount_rate,
            'points_multiplier': str(level.points_multiplier),
            'description': level.description,
        },
        'next_level': {
            'level': next_level.level,
            'name': next_level.name,
            'min_points': next_level.min_points,
        } if next_level else None,
        'growth_points': profile.growth_points,
        'checkin_streak': profile.checkin_streak,
        'total_checkins': profile.total_checkins,
        'checked_in_today': checked_in_today,
        'progress_percent': progress_percent,
        'points_to_next': points_to_next,
        'benefits_text': _format_benefits(level),
    }


def _format_benefits(level: MemberLevel) -> str:
    parts = []
    if level.discount_rate < 100:
        parts.append(f'{level.discount_rate}折')
    multiplier = float(level.points_multiplier)
    if multiplier > 1:
        parts.append(f'{multiplier:g}倍积分')
    return ' + '.join(parts) if parts else '基础权益'
