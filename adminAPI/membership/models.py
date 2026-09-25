"""Membership level models."""

from django.db import models


class MemberLevel(models.Model):
    """Configurable membership tier."""

    level = models.PositiveSmallIntegerField('等级值', unique=True)
    name = models.CharField('等级名称', max_length=32)
    min_points = models.PositiveIntegerField('所需成长值', default=0)
    discount_rate = models.PositiveSmallIntegerField(
        '折扣率(%)',
        default=100,
        help_text='100 表示无折扣，88 表示 88 折',
    )
    points_multiplier = models.DecimalField(
        '积分加速倍率',
        max_digits=4,
        decimal_places=2,
        default=1.00,
    )
    description = models.CharField('权益说明', max_length=255, blank=True, default='')
    sort_order = models.PositiveSmallIntegerField('排序', default=0)
    is_active = models.BooleanField('启用', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'membership_level'
        verbose_name = '会员等级'
        verbose_name_plural = verbose_name
        ordering = ['level']

    def __str__(self) -> str:
        return self.name


class MemberProfile(models.Model):
    """Per-customer membership progress."""

    customer = models.OneToOneField(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='member_profile',
        verbose_name='客户',
    )
    current_level = models.ForeignKey(
        MemberLevel,
        on_delete=models.PROTECT,
        related_name='members',
        verbose_name='当前等级',
    )
    growth_points = models.PositiveIntegerField('成长值', default=0)
    checkin_streak = models.PositiveIntegerField('连续签到天数', default=0)
    total_checkins = models.PositiveIntegerField('累计签到天数', default=0)
    last_checkin_date = models.DateField('最近签到日期', null=True, blank=True)
    level_upgraded_at = models.DateTimeField('最近升级时间', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'membership_profile'
        verbose_name = '会员档案'
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f'{self.customer_id}-{self.current_level.name}'


class GrowthLog(models.Model):
    """Growth points ledger."""

    TYPE_SIGN_IN = 'sign_in'
    TYPE_ORDER = 'order'
    TYPE_REVIEW = 'review'
    TYPE_PROFILE = 'profile'
    TYPE_LEVEL_UP = 'level_up'
    TYPE_ADMIN = 'admin'

    TYPE_CHOICES = [
        (TYPE_SIGN_IN, '签到'),
        (TYPE_ORDER, '消费'),
        (TYPE_REVIEW, '评价'),
        (TYPE_PROFILE, '完善资料'),
        (TYPE_LEVEL_UP, '等级升级'),
        (TYPE_ADMIN, '管理员调整'),
    ]

    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='growth_logs',
        verbose_name='客户',
    )
    amount = models.IntegerField('变动成长值')
    balance_after = models.PositiveIntegerField('变动后成长值')
    log_type = models.CharField('类型', max_length=16, choices=TYPE_CHOICES)
    description = models.CharField('说明', max_length=255, blank=True, default='')
    source = models.CharField('来源标识', max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'membership_growth_log'
        verbose_name = '成长值明细'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self) -> str:
        return f'{self.customer_id}:{self.log_type}:{self.amount}'
