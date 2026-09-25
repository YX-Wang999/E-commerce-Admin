"""Points account, transaction and rule models."""

from decimal import Decimal

from django.db import models

from common.tenant import TenantAwareManager


class PointsAccount(models.Model):
    """Customer points balance summary."""

    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='points_accounts',
        verbose_name='会员',
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='points_accounts',
        null=True,
        blank=True,
        verbose_name='商家',
    )
    balance = models.PositiveIntegerField(default=0, verbose_name='可用积分')
    total_earned = models.PositiveIntegerField(default=0, verbose_name='累计获得')
    total_spent = models.PositiveIntegerField(default=0, verbose_name='累计消耗')
    balance_expire_at = models.DateTimeField(null=True, blank=True, verbose_name='积分过期时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    objects = TenantAwareManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'points_account'
        verbose_name = '积分账户'
        verbose_name_plural = verbose_name
        unique_together = [('customer', 'tenant')]

    def __str__(self) -> str:
        return f'{self.customer.name}-{self.balance}'


class PointsTransaction(models.Model):
    """Points ledger entry."""

    TYPE_EARN_SIGN_IN = 'earn_sign_in'
    TYPE_EARN_ORDER = 'earn_order'
    TYPE_EARN_REVIEW = 'earn_review'
    TYPE_SPEND_REDEEM = 'spend_redeem'
    TYPE_ADJUST_ADMIN = 'adjust_admin'
    TYPE_SPEND_CHECKOUT = 'spend_checkout'
    TYPE_SPEND_EXPIRE = 'spend_expire'
    TYPE_REFUND_ORDER = 'refund_order'
    TYPE_CHOICES = [
        (TYPE_EARN_SIGN_IN, '签到奖励'),
        (TYPE_EARN_ORDER, '订单奖励'),
        (TYPE_EARN_REVIEW, '评价奖励'),
        (TYPE_SPEND_REDEEM, '积分兑换'),
        (TYPE_SPEND_CHECKOUT, '下单抵扣'),
        (TYPE_SPEND_EXPIRE, '积分过期'),
        (TYPE_ADJUST_ADMIN, '管理员调整'),
        (TYPE_REFUND_ORDER, '订单退还'),
    ]

    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='points_transactions',
        verbose_name='会员',
    )
    amount = models.IntegerField(verbose_name='变动数量')
    balance_after = models.PositiveIntegerField(verbose_name='变动后余额')
    trans_type = models.CharField(max_length=32, choices=TYPE_CHOICES, verbose_name='类型')
    source = models.CharField(max_length=64, blank=True, default='', verbose_name='来源标识')
    description = models.CharField(max_length=255, blank=True, default='', verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'points_transaction'
        verbose_name = '积分流水'
        verbose_name_plural = verbose_name
        ordering = ['-id']
        indexes = [
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['source']),
        ]

    def __str__(self) -> str:
        return f'{self.customer_id}:{self.amount}'


class PointsRule(models.Model):
    """Configurable points rule."""

    RULE_EARN = 'earn'
    RULE_REDEEM = 'redeem'
    RULE_TYPES = [
        (RULE_EARN, '赚取积分'),
        (RULE_REDEEM, '消耗积分'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='规则编码')
    name = models.CharField(max_length=100, verbose_name='规则名称')
    description = models.TextField(blank=True, default='', verbose_name='说明')
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES, default=RULE_EARN, verbose_name='规则类型')

    default_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='默认值')
    current_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='当前值')

    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='最小值')
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='最大值')

    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    is_system = models.BooleanField(default=False, verbose_name='系统内置')
    trigger_config = models.JSONField(default=dict, blank=True, verbose_name='触发配置')
    sort_order = models.IntegerField(default=0, verbose_name='排序')

    # legacy column kept for migration compatibility
    points_value = models.PositiveIntegerField(default=0, verbose_name='积分值(旧)')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'points_rule'
        verbose_name = '积分规则'
        verbose_name_plural = verbose_name
        ordering = ['rule_type', 'sort_order', 'id']

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if self.current_value is None:
            self.current_value = self.default_value
        self.points_value = int(self.current_value or 0)
        super().save(*args, **kwargs)

    def clamp_value(self, value: Decimal) -> Decimal:
        result = value
        if self.min_value is not None:
            result = max(result, self.min_value)
        if self.max_value is not None:
            result = min(result, self.max_value)
        return result


class PointsSignInRecord(models.Model):
    """Daily sign-in record."""

    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='sign_in_records',
        verbose_name='会员',
    )
    sign_date = models.DateField(verbose_name='签到日期')
    consecutive_days = models.PositiveIntegerField(default=1, verbose_name='连续签到天数')
    points_earned = models.PositiveIntegerField(default=0, verbose_name='获得积分')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'points_sign_in_record'
        verbose_name = '签到记录'
        verbose_name_plural = verbose_name
        unique_together = [('customer', 'sign_date')]
