"""Shop rating models."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ShopRating(models.Model):
    """店铺综合评分."""

    tenant = models.OneToOneField(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='shop_rating',
        verbose_name='商家',
    )
    overall_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=5.0,
        verbose_name='综合评分',
    )
    quality_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=5.0,
        verbose_name='商品质量',
    )
    service_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=5.0,
        verbose_name='服务态度',
    )
    logistics_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=5.0,
        verbose_name='物流速度',
    )
    total_ratings = models.PositiveIntegerField(default=0, verbose_name='评价总数')
    total_orders = models.PositiveIntegerField(default=0, verbose_name='总订单数')
    completed_orders = models.PositiveIntegerField(default=0, verbose_name='已完成订单')
    refund_orders = models.PositiveIntegerField(default=0, verbose_name='退款订单')
    initial_score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=5.0,
        verbose_name='初始评分',
    )
    initial_weight_threshold = models.PositiveIntegerField(
        default=10,
        verbose_name='初始分衰减阈值',
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'shop_rating_shop_rating'
        verbose_name = '店铺评分'
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f'{self.tenant_id}-{self.overall_score}'


class UserRating(models.Model):
    """用户评价记录."""

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='user_ratings',
        verbose_name='商家',
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='shop_ratings',
        verbose_name='会员',
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='shop_ratings',
        verbose_name='关联订单',
    )
    product_review = models.OneToOneField(
        'reviews.ProductReview',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='shop_user_rating',
        verbose_name='商品评价',
    )
    quality_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='商品质量评分',
    )
    service_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='服务态度评分',
    )
    logistics_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='物流速度评分',
    )
    content = models.TextField(blank=True, default='', verbose_name='评价内容')
    images = models.JSONField(default=list, blank=True, verbose_name='评价图片')
    is_anonymous = models.BooleanField(default=False, verbose_name='是否匿名')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'shop_rating_user_rating'
        verbose_name = '用户评价'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self) -> str:
        return f'{self.tenant_id}-{self.customer_id}'


class RatingAdjustmentLog(models.Model):
    """评分调整日志."""

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='rating_logs',
        verbose_name='商家',
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shop_rating_adjustments',
        verbose_name='操作人',
    )
    old_score = models.DecimalField(max_digits=3, decimal_places=1, verbose_name='原评分')
    new_score = models.DecimalField(max_digits=3, decimal_places=1, verbose_name='新评分')
    reason = models.CharField(max_length=200, verbose_name='调整原因')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'shop_rating_adjustment_log'
        verbose_name = '评分调整日志'
        verbose_name_plural = verbose_name
        ordering = ['-id']


class RatingAdjustmentRequest(models.Model):
    """商家评分调整申请."""

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待审核'),
        (STATUS_APPROVED, '已通过'),
        (STATUS_REJECTED, '已驳回'),
    ]

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='rating_adjustment_requests',
        verbose_name='商家',
    )
    current_score = models.DecimalField(max_digits=3, decimal_places=1, verbose_name='当前评分')
    requested_score = models.DecimalField(max_digits=3, decimal_places=1, verbose_name='申请评分')
    reason = models.CharField(max_length=200, verbose_name='申请理由')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='状态',
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_rating_requests',
        verbose_name='审核人',
    )
    review_note = models.CharField(max_length=200, blank=True, default='', verbose_name='审核备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='申请时间')
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')

    class Meta:
        db_table = 'shop_rating_adjustment_request'
        verbose_name = '评分调整申请'
        verbose_name_plural = verbose_name
        ordering = ['-id']


class RatingScoreHistory(models.Model):
    """评分历史（趋势图）."""

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='rating_history',
        verbose_name='商家',
    )
    overall_score = models.DecimalField(max_digits=3, decimal_places=1, verbose_name='综合评分')
    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name='记录时间')

    class Meta:
        db_table = 'shop_rating_score_history'
        verbose_name = '评分历史'
        verbose_name_plural = verbose_name
        ordering = ['-recorded_at']
