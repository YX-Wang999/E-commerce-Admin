"""Order models."""

from django.conf import settings
from django.db import models

from common.tenant import TenantAwareManager
from customers.models import Customer
from products.models import Product

class Order(models.Model):
    """Sales order."""

    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_SHIPPED = 'shipped'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_REFUNDING = 'refunding'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待支付'),
        (STATUS_PAID, '待发货'),
        (STATUS_SHIPPED, '已发货'),
        (STATUS_COMPLETED, '已完成'),
        (STATUS_CANCELLED, '已取消'),
        (STATUS_REFUNDING, '退款中'),
    ]

    CANCEL_TYPE_USER = 'user'
    CANCEL_TYPE_TIMEOUT = 'timeout'
    CANCEL_TYPE_MERCHANT = 'merchant'
    CANCEL_TYPE_PLATFORM = 'platform'
    CANCEL_TYPE_GROUPBUY = 'groupbuy'

    CANCEL_TYPE_CHOICES = [
        (CANCEL_TYPE_USER, '用户取消'),
        (CANCEL_TYPE_TIMEOUT, '支付超时'),
        (CANCEL_TYPE_MERCHANT, '商户取消'),
        (CANCEL_TYPE_PLATFORM, '平台取消'),
        (CANCEL_TYPE_GROUPBUY, '团购失败'),
    ]

    CANCEL_STATUS_NONE = ''
    CANCEL_STATUS_PENDING = 'pending'
    CANCEL_STATUS_REJECTED = 'rejected'

    CANCEL_STATUS_CHOICES = [
        (CANCEL_STATUS_NONE, '无'),
        (CANCEL_STATUS_PENDING, '取消审核中'),
        (CANCEL_STATUS_REJECTED, '取消已驳回'),
    ]

    order_no = models.CharField(max_length=32, unique=True, verbose_name='订单号')
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='客户',
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='orders',
        null=True,
        blank=True,
        verbose_name='商家',
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='总金额')
    original_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='商品原价合计',
    )
    coupon_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='优惠券抵扣',
    )
    points_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='积分抵扣',
    )
    points_used = models.PositiveIntegerField(default=0, verbose_name='使用积分')
    seller_points_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='商家积分抵扣',
    )
    seller_points_used = models.PositiveIntegerField(default=0, verbose_name='使用商家积分')
    user_coupon = models.ForeignKey(
        'promotion.UserCoupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='使用优惠券',
    )
    promotion_type = models.CharField(
        max_length=16,
        blank=True,
        default='',
        verbose_name='促销类型',
    )
    promotion_ref = models.CharField(
        max_length=64,
        blank=True,
        default='',
        verbose_name='促销关联',
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='订单状态',
    )
    address = models.CharField(max_length=255, verbose_name='收货地址')
    logistics_no = models.CharField(max_length=64, blank=True, default='', verbose_name='物流单号')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_orders',
        verbose_name='负责人',
    )
    remark = models.CharField(max_length=255, blank=True, default='', verbose_name='备注')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='支付时间')
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='支付截止时间')
    cancel_status = models.CharField(
        '取消审核状态',
        max_length=16,
        choices=CANCEL_STATUS_CHOICES,
        blank=True,
        default=CANCEL_STATUS_NONE,
    )
    cancel_type = models.CharField(
        '取消类型',
        max_length=16,
        choices=CANCEL_TYPE_CHOICES,
        blank=True,
        default='',
    )
    cancel_reason = models.CharField('取消原因', max_length=255, blank=True, default='')
    cancel_detail = models.CharField('取消说明', max_length=255, blank=True, default='')
    cancel_review_remark = models.CharField('取消审核备注', max_length=255, blank=True, default='')
    cancelled_at = models.DateTimeField(null=True, blank=True, verbose_name='取消时间')
    shipped_at = models.DateTimeField(null=True, blank=True, verbose_name='发货时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    RECEIPT_TYPE_NORMAL = 'normal'
    RECEIPT_TYPE_EARLY = 'early'
    RECEIPT_TYPE_AUTO = 'auto'
    RECEIPT_TYPE_CHOICES = [
        ('', '无'),
        (RECEIPT_TYPE_NORMAL, '正常签收'),
        (RECEIPT_TYPE_EARLY, '提前签收'),
        (RECEIPT_TYPE_AUTO, '自动确认'),
    ]
    receipt_type = models.CharField(
        max_length=16,
        choices=RECEIPT_TYPE_CHOICES,
        blank=True,
        default='',
        verbose_name='签收方式',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    objects = TenantAwareManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'orders_order'
        verbose_name = '订单'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self) -> str:
        return self.order_no


class OrderItem(models.Model):
    """Order line item."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='订单',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='商品',
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name='数量')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='单价')
    product_name = models.CharField(max_length=128, blank=True, default='', verbose_name='商品名称快照')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'orders_order_item'
        verbose_name = '订单明细'
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f'{self.order.order_no}-{self.product.name}'


class Refund(models.Model):
    """Refund application."""

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待审核'),
        (STATUS_APPROVED, '已通过'),
        (STATUS_REJECTED, '已拒绝'),
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='refunds',
        verbose_name='订单',
    )
    reason = models.CharField(max_length=255, verbose_name='退款原因')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='退款金额')
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='状态',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='申请时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'orders_refund'
        verbose_name = '退款申请'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self) -> str:
        return f'{self.order.order_no}-refund'


class CancelLog(models.Model):
    """Audit trail for order cancellation events."""

    ACTION_AUTO = 'auto'
    ACTION_USER_DIRECT = 'user_direct'
    ACTION_USER_APPLY = 'user_apply'
    ACTION_MERCHANT_APPROVE = 'merchant_approve'
    ACTION_MERCHANT_REJECT = 'merchant_reject'
    ACTION_MERCHANT_CANCEL = 'merchant_cancel'
    ACTION_PLATFORM_CANCEL = 'platform_cancel'

    ACTION_CHOICES = [
        (ACTION_AUTO, '系统自动'),
        (ACTION_USER_DIRECT, '用户直接取消'),
        (ACTION_USER_APPLY, '用户申请取消'),
        (ACTION_MERCHANT_APPROVE, '商户同意取消'),
        (ACTION_MERCHANT_REJECT, '商户驳回取消'),
        (ACTION_MERCHANT_CANCEL, '商户主动取消'),
        (ACTION_PLATFORM_CANCEL, '平台强制取消'),
    ]

    OPERATOR_CUSTOMER = 'customer'
    OPERATOR_MERCHANT = 'merchant'
    OPERATOR_STAFF = 'staff'
    OPERATOR_SYSTEM = 'system'

    OPERATOR_CHOICES = [
        (OPERATOR_CUSTOMER, '用户'),
        (OPERATOR_MERCHANT, '商户'),
        (OPERATOR_STAFF, '平台'),
        (OPERATOR_SYSTEM, '系统'),
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='cancel_logs',
        verbose_name='订单',
    )
    action = models.CharField('操作类型', max_length=32, choices=ACTION_CHOICES)
    reason = models.CharField('原因', max_length=255, blank=True, default='')
    remark = models.CharField('备注', max_length=255, blank=True, default='')
    operator_type = models.CharField(
        '操作方',
        max_length=16,
        choices=OPERATOR_CHOICES,
        default=OPERATOR_SYSTEM,
    )
    operator_id = models.CharField('操作人标识', max_length=64, blank=True, default='')
    created_at = models.DateTimeField('记录时间', auto_now_add=True)

    class Meta:
        db_table = 'orders_cancel_log'
        verbose_name = '订单取消日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.order.order_no}-{self.action}'
