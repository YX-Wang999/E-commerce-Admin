"""Promotion models."""

from django.conf import settings
from django.db import models

from common.tenant import TenantAwareManager
from products.models import Product


class SeckillActivity(models.Model):
    """Flash sale (seckill) activity."""

    STATUS_PENDING = 'pending'
    STATUS_REVIEWING = 'reviewing'
    STATUS_RUNNING = 'running'
    STATUS_ENDED = 'ended'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, '待审核'),
        (STATUS_REVIEWING, '审核中'),
        (STATUS_RUNNING, '进行中'),
        (STATUS_ENDED, '已结束'),
        (STATUS_CANCELLED, '已取消'),
    ]

    name = models.CharField('活动名称', max_length=128)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='seckill_activities',
        null=True,
        blank=True,
        verbose_name='商家',
    )
    products = models.ManyToManyField(Product, related_name='seckill_activities', verbose_name='参与商品')
    seckill_price = models.DecimalField('秒杀价', max_digits=10, decimal_places=2)
    seckill_stock = models.PositiveIntegerField('秒杀库存')
    per_user_limit = models.PositiveIntegerField('每人限购', default=1)
    start_time = models.DateTimeField('开始时间')
    end_time = models.DateTimeField('结束时间')
    warmup_time = models.DateTimeField('预热时间', null=True, blank=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reject_reason = models.CharField('驳回原因', max_length=255, blank=True, default='')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_seckills',
        verbose_name='审批人',
    )
    approved_at = models.DateTimeField('审批时间', null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_seckills',
        verbose_name='创建人',
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    objects = TenantAwareManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'promotion_seckill_activity'
        verbose_name = '秒杀活动'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.name


class GroupBuyActivity(models.Model):
    """Group buy activity."""

    STATUS_PENDING = 'pending'
    STATUS_REVIEWING = 'reviewing'
    STATUS_RUNNING = 'running'
    STATUS_ENDED = 'ended'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, '待审核'),
        (STATUS_REVIEWING, '审核中'),
        (STATUS_RUNNING, '进行中'),
        (STATUS_ENDED, '已结束'),
        (STATUS_CANCELLED, '已取消'),
    ]

    name = models.CharField('活动名称', max_length=128)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='groupbuy_activities',
        null=True,
        blank=True,
        verbose_name='商家',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='groupbuy_activities',
        verbose_name='拼团商品',
    )
    group_price = models.DecimalField('团购价', max_digits=10, decimal_places=2)
    group_size = models.PositiveIntegerField('成团人数', default=3)
    stock = models.PositiveIntegerField('活动库存')
    per_user_limit = models.PositiveIntegerField('每人限购', default=5)
    group_valid_hours = models.PositiveIntegerField('拼团有效期(小时)', default=24)
    auto_group = models.BooleanField('虚拟成团', default=False)
    start_time = models.DateTimeField('开始时间')
    end_time = models.DateTimeField('结束时间')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reject_reason = models.CharField('驳回原因', max_length=255, blank=True, default='')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_groupbuys',
        verbose_name='审批人',
    )
    approved_at = models.DateTimeField('审批时间', null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_groupbuys',
        verbose_name='创建人',
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    objects = TenantAwareManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'promotion_groupbuy_activity'
        verbose_name = '团购活动'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.name


class GroupOrder(models.Model):
    """Group buy order record."""

    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, '拼团中'),
        (STATUS_SUCCESS, '已成团'),
        (STATUS_FAILED, '拼团失败'),
    ]

    activity = models.ForeignKey(
        GroupBuyActivity,
        on_delete=models.CASCADE,
        related_name='group_orders',
        verbose_name='团购活动',
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='group_orders',
        verbose_name='订单',
    )
    captain = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='captain_group_orders',
        verbose_name='团长',
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='member_group_orders',
        blank=True,
        verbose_name='团员',
    )
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    expired_at = models.DateTimeField('拼团截止时间')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'promotion_group_order'
        verbose_name = '拼团订单'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.activity.name}-{self.order_id}'


class Coupon(models.Model):
    """Coupon template."""

    TYPE_FIXED = 'fixed'
    TYPE_DISCOUNT = 'discount'
    TYPE_FREE = 'free'

    TYPE_CHOICES = [
        (TYPE_FIXED, '满减券'),
        (TYPE_DISCOUNT, '折扣券'),
        (TYPE_FREE, '无门槛券'),
    ]

    SCOPE_ALL = 'all'
    SCOPE_CATEGORY = 'category'
    SCOPE_PRODUCT = 'product'

    SCOPE_CHOICES = [
        (SCOPE_ALL, '全部商品'),
        (SCOPE_CATEGORY, '指定分类'),
        (SCOPE_PRODUCT, '指定商品'),
    ]

    VALID_FIXED = 'fixed'
    VALID_AFTER_RECEIVE = 'after_receive'

    VALID_TYPE_CHOICES = [
        (VALID_FIXED, '固定时间'),
        (VALID_AFTER_RECEIVE, '领取后有效'),
    ]

    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_EXPIRED = 'expired'
    STATUS_DISABLED = 'disabled'

    STATUS_CHOICES = [
        (STATUS_DRAFT, '草稿'),
        (STATUS_PUBLISHED, '已发布'),
        (STATUS_EXPIRED, '已过期'),
        (STATUS_DISABLED, '已停用'),
    ]

    name = models.CharField('优惠券名称', max_length=128)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='coupons',
        null=True,
        blank=True,
        verbose_name='商家',
    )
    coupon_type = models.CharField('类型', max_length=20, choices=TYPE_CHOICES, default=TYPE_FIXED)
    discount_amount = models.DecimalField('满减金额', max_digits=10, decimal_places=2, null=True, blank=True)
    discount_rate = models.DecimalField('折扣率', max_digits=5, decimal_places=2, null=True, blank=True)
    max_discount = models.DecimalField('最大折扣金额', max_digits=10, decimal_places=2, null=True, blank=True)
    min_amount = models.DecimalField('使用门槛', max_digits=10, decimal_places=2, default=0)
    total_quantity = models.PositiveIntegerField('发放总量')
    per_user_limit = models.PositiveIntegerField('每人限领', default=1)
    applicable_scope = models.CharField(
        '适用范围',
        max_length=20,
        choices=SCOPE_CHOICES,
        default=SCOPE_ALL,
    )
    applicable_category = models.ForeignKey(
        'products.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coupons',
        verbose_name='适用分类',
    )
    applicable_products = models.ManyToManyField(
        Product,
        blank=True,
        related_name='coupons',
        verbose_name='适用商品',
    )
    valid_type = models.CharField('有效期类型', max_length=20, choices=VALID_TYPE_CHOICES, default=VALID_FIXED)
    valid_start = models.DateTimeField('有效开始', null=True, blank=True)
    valid_end = models.DateTimeField('有效结束', null=True, blank=True)
    valid_days = models.PositiveIntegerField('领取后有效天数', null=True, blank=True)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_coupons',
        verbose_name='创建人',
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    objects = TenantAwareManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'promotion_coupon'
        verbose_name = '优惠券'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.name


class UserCoupon(models.Model):
    """User coupon receive record."""

    STATUS_UNUSED = 'unused'
    STATUS_USED = 'used'
    STATUS_EXPIRED = 'expired'

    STATUS_CHOICES = [
        (STATUS_UNUSED, '未使用'),
        (STATUS_USED, '已使用'),
        (STATUS_EXPIRED, '已过期'),
    ]

    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='user_coupons', verbose_name='优惠券')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_coupons',
        null=True,
        blank=True,
        verbose_name='用户',
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='user_coupons',
        null=True,
        blank=True,
        verbose_name='商城会员',
    )
    code = models.CharField('券码', max_length=32, unique=True)
    received_at = models.DateTimeField('领取时间', auto_now_add=True)
    used_at = models.DateTimeField('使用时间', null=True, blank=True)
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='used_coupons',
        verbose_name='使用订单',
    )
    expired_at = models.DateTimeField('过期时间')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default=STATUS_UNUSED)

    class Meta:
        db_table = 'promotion_user_coupon'
        verbose_name = '用户优惠券'
        verbose_name_plural = verbose_name
        ordering = ['-received_at']

    def __str__(self) -> str:
        return self.code


class SuperDiscount(models.Model):
    """Platform-managed super discount campaign for mall home."""

    title = models.CharField('活动标题', max_length=64, default='超级立减')
    promo_text = models.CharField('宣传文案', max_length=128, default='限时立减')
    amount = models.DecimalField('立减金额', max_digits=10, decimal_places=2, default=15)
    button_text = models.CharField('按钮文案', max_length=32, default='立即领取')
    link_url = models.CharField('跳转链接', max_length=255, blank=True, default='')
    is_active = models.BooleanField('启用', default=True)
    start_time = models.DateTimeField('开始时间', null=True, blank=True)
    end_time = models.DateTimeField('结束时间', null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_super_discounts',
        verbose_name='创建人',
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'promotion_super_discount'
        verbose_name = '超级立减'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self) -> str:
        return self.title
