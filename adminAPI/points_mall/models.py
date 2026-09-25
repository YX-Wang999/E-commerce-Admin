"""Points mall product and exchange order models."""

from django.db import models


class PointsMallItem(models.Model):
    """Redeemable item in the points mall."""

    TYPE_PHYSICAL = 'physical'
    TYPE_COUPON = 'coupon'
    TYPE_BENEFIT = 'benefit'
    TYPE_LOTTERY = 'lottery'
    TYPE_CHOICES = [
        (TYPE_PHYSICAL, '实物'),
        (TYPE_COUPON, '优惠券'),
        (TYPE_BENEFIT, '权益'),
        (TYPE_LOTTERY, '抽奖'),
    ]

    STATUS_DRAFT = 'draft'
    STATUS_ON_SALE = 'on_sale'
    STATUS_OFF_SALE = 'off_sale'
    STATUS_CHOICES = [
        (STATUS_DRAFT, '草稿'),
        (STATUS_ON_SALE, '上架'),
        (STATUS_OFF_SALE, '下架'),
    ]

    name = models.CharField(max_length=120, verbose_name='商品名称')
    image = models.CharField(max_length=500, blank=True, default='', verbose_name='图片')
    description = models.TextField(blank=True, default='', verbose_name='描述')
    item_type = models.CharField(max_length=16, choices=TYPE_CHOICES, default=TYPE_PHYSICAL, db_index=True)
    points_required = models.PositiveIntegerField(verbose_name='所需积分')
    stock = models.PositiveIntegerField(default=0, verbose_name='库存')
    exchanged_count = models.PositiveIntegerField(default=0, verbose_name='已兑换数')
    per_user_limit = models.PositiveIntegerField(default=1, verbose_name='每人限购')
    requires_address = models.BooleanField(default=False, verbose_name='需要收货地址')
    coupon_template = models.ForeignKey(
        'promotion.Coupon',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='points_mall_items',
        verbose_name='关联优惠券',
    )
    is_hot = models.BooleanField(default=False, verbose_name='热销')
    is_limited_time = models.BooleanField(default=False, verbose_name='限时')
    start_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    end_at = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'points_mall_item'
        verbose_name = '积分商品'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', '-id']

    def __str__(self) -> str:
        return self.name


class PointsMallOrder(models.Model):
    """Points mall exchange order."""

    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_SHIPPED = 'shipped'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待处理'),
        (STATUS_PROCESSING, '处理中'),
        (STATUS_SHIPPED, '已发货'),
        (STATUS_COMPLETED, '已完成'),
        (STATUS_CANCELLED, '已取消'),
    ]

    order_no = models.CharField(max_length=32, unique=True, verbose_name='兑换单号')
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='points_mall_orders',
        verbose_name='会员',
    )
    item = models.ForeignKey(
        PointsMallItem,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='商品',
    )
    item_name = models.CharField(max_length=120, verbose_name='商品名称快照')
    item_type = models.CharField(max_length=16, verbose_name='商品类型快照')
    points_spent = models.PositiveIntegerField(verbose_name='消耗积分')
    quantity = models.PositiveIntegerField(default=1, verbose_name='数量')
    address = models.JSONField(default=dict, blank=True, verbose_name='收货地址')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    logistics_company = models.CharField(max_length=64, blank=True, default='', verbose_name='物流公司')
    logistics_no = models.CharField(max_length=64, blank=True, default='', verbose_name='物流单号')
    coupon_code = models.CharField(max_length=64, blank=True, default='', verbose_name='券码')
    remark = models.CharField(max_length=255, blank=True, default='', verbose_name='备注')
    shipped_at = models.DateTimeField(null=True, blank=True, verbose_name='发货时间')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'points_mall_order'
        verbose_name = '积分兑换订单'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self) -> str:
        return self.order_no
