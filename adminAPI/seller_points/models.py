"""Seller-specific points models — independent from platform points."""

from django.db import models


class SellerPointsRule(models.Model):
    """Per-tenant shop points configuration."""

    tenant = models.OneToOneField(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='seller_points_rule',
        verbose_name='商家',
    )
    earn_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
        verbose_name='消费送积分比例',
        help_text='每消费1元送多少积分',
    )
    max_earn_per_order = models.PositiveIntegerField(
        default=1000,
        verbose_name='单笔订单最大获取积分',
    )
    redeem_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=100.00,
        verbose_name='积分兑换比例',
        help_text='多少积分抵1元',
    )
    max_redeem_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=30.00,
        verbose_name='最大抵扣比例(%)',
        help_text='最多可抵订单金额的百分比',
    )
    expire_days = models.PositiveIntegerField(default=365, verbose_name='积分有效期(天)')
    points_name = models.CharField(max_length=50, default='店铺积分', verbose_name='积分名称')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'seller_points_rule'
        verbose_name = '商家积分规则'
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f'{self.tenant_id}-{self.points_name}'


class SellerPointsAccount(models.Model):
    """Shop points balance for a customer at a tenant."""

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='seller_points_accounts',
        verbose_name='商家',
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='seller_points_accounts',
        verbose_name='客户',
    )
    balance = models.PositiveIntegerField(default=0, verbose_name='当前积分余额')
    total_earned = models.PositiveIntegerField(default=0, verbose_name='累计获得')
    total_spent = models.PositiveIntegerField(default=0, verbose_name='累计消耗')
    expire_at = models.DateTimeField(null=True, blank=True, verbose_name='积分过期时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'seller_points_account'
        verbose_name = '商家积分账户'
        verbose_name_plural = verbose_name
        unique_together = [('tenant', 'customer')]

    def __str__(self) -> str:
        return f'{self.tenant_id}:{self.customer_id}={self.balance}'


class SellerPointsTransaction(models.Model):
    """Shop points ledger."""

    TYPE_EARN_ORDER = 'earn_order'
    TYPE_REDEEM_ORDER = 'redeem_order'
    TYPE_EXPIRE = 'expire'
    TYPE_ADMIN_ADJUST = 'admin_adjust'
    TYPE_REFUND_ORDER = 'refund_order'
    TYPE_CHOICES = [
        (TYPE_EARN_ORDER, '订单奖励'),
        (TYPE_REDEEM_ORDER, '订单抵扣'),
        (TYPE_EXPIRE, '过期扣除'),
        (TYPE_ADMIN_ADJUST, '商家调整'),
        (TYPE_REFUND_ORDER, '订单退还'),
    ]

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='seller_points_transactions',
        verbose_name='商家',
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='seller_points_transactions',
        verbose_name='客户',
    )
    account = models.ForeignKey(
        SellerPointsAccount,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='账户',
    )
    amount = models.IntegerField(verbose_name='变动数量')
    balance_after = models.PositiveIntegerField(verbose_name='变动后余额')
    trans_type = models.CharField(max_length=32, choices=TYPE_CHOICES, verbose_name='类型')
    source_id = models.CharField(max_length=100, blank=True, default='', verbose_name='来源ID')
    description = models.CharField(max_length=200, blank=True, default='', verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'seller_points_transaction'
        verbose_name = '商家积分流水'
        verbose_name_plural = verbose_name
        ordering = ['-id']
        indexes = [
            models.Index(fields=['tenant', '-created_at']),
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['source_id']),
        ]

    def __str__(self) -> str:
        return f'{self.tenant_id}:{self.amount}'
