"""National subsidy models."""

from django.conf import settings
from django.db import models

from products.models import Product


class SubsidyPolicy(models.Model):
    """Platform subsidy policy configuration (government standard reference)."""

    TYPE_PERCENT = 'percent'
    TYPE_FIXED = 'fixed'

    TYPE_CHOICES = [
        (TYPE_PERCENT, '按比例'),
        (TYPE_FIXED, '固定金额'),
    ]

    name = models.CharField('政策名称', max_length=128)
    description = models.TextField('政策说明', blank=True, default='')
    subsidy_type = models.CharField(
        '补贴类型',
        max_length=16,
        choices=TYPE_CHOICES,
        default=TYPE_PERCENT,
    )
    subsidy_value = models.DecimalField('补贴值', max_digits=10, decimal_places=2)
    max_subsidy = models.DecimalField(
        '单笔最高补贴',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    region = models.CharField('适用地区', max_length=64, blank=True, default='')
    category = models.CharField('适用品类', max_length=64, blank=True, default='')
    is_active = models.BooleanField('是否启用', default=True)
    start_time = models.DateTimeField('生效开始', null=True, blank=True)
    end_time = models.DateTimeField('生效结束', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'subsidy_policy'
        verbose_name = '国补政策'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.name


class SubsidyProduct(models.Model):
    """Government filing record for a merchant product (platform does not audit)."""

    FILING_NOT_SUBMITTED = 'not_submitted'
    FILING_SUBMITTED = 'submitted'
    FILING_APPROVED = 'approved'
    FILING_REJECTED = 'rejected'

    FILING_CHOICES = [
        (FILING_NOT_SUBMITTED, '未备案'),
        (FILING_SUBMITTED, '已提交备案'),
        (FILING_APPROVED, '已备案通过'),
        (FILING_REJECTED, '备案驳回'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='subsidy_applications',
        verbose_name='商品',
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='subsidy_products',
        verbose_name='商家',
    )
    policy = models.ForeignKey(
        SubsidyPolicy,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='适用政策',
    )
    region = models.CharField('活动地区', max_length=64, blank=True, default='')
    category = models.CharField('补贴品类', max_length=64, blank=True, default='')
    filing_status = models.CharField(
        '备案状态',
        max_length=20,
        choices=FILING_CHOICES,
        default=FILING_NOT_SUBMITTED,
    )
    subsidy_amount = models.DecimalField(
        '补贴金额',
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    filing_submitted_at = models.DateTimeField('备案提交时间', null=True, blank=True)
    filing_reject_reason = models.TextField('备案驳回原因', blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'subsidy_product'
        verbose_name = '国补商品备案'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['product'], name='uniq_subsidy_product'),
        ]

    def __str__(self) -> str:
        return f'{self.product_id} ({self.get_filing_status_display()})'


class SubsidyOrder(models.Model):
    """National subsidy order extension — SN/IMEI and government reporting."""

    GOV_PENDING = 'pending'
    GOV_REPORTED = 'reported'
    GOV_VERIFIED = 'verified'
    GOV_FAILED = 'failed'

    GOV_STATUS_CHOICES = [
        (GOV_PENDING, '待上报'),
        (GOV_REPORTED, '已上报'),
        (GOV_VERIFIED, '核验通过'),
        (GOV_FAILED, '核验失败'),
    ]

    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='subsidy_order',
        verbose_name='订单',
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='subsidy_orders',
        verbose_name='商家',
    )
    sn_code = models.CharField('SN码', max_length=100, blank=True, default='')
    imei_code = models.CharField('IMEI码', max_length=200, blank=True, default='')
    government_status = models.CharField(
        '政府核验状态',
        max_length=20,
        choices=GOV_STATUS_CHOICES,
        default=GOV_PENDING,
    )
    reported_at = models.DateTimeField('上报时间', null=True, blank=True)
    fail_reason = models.CharField('核验失败原因', max_length=255, blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'subsidy_order'
        verbose_name = '国补订单'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'国补订单 #{self.order_id}'
