"""Product models."""

from django.conf import settings
from django.db import models

from common.tenant import TenantAwareManager


class Category(models.Model):
    """Product category tree."""

    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name='父级分类',
    )
    name = models.CharField(max_length=64, verbose_name='分类名称')
    icon = models.CharField(max_length=64, blank=True, default='', verbose_name='分类图标')
    sort_order = models.PositiveIntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'products_category'
        verbose_name = '商品分类'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return self.name


class Brand(models.Model):
    """Product brand."""

    name = models.CharField(max_length=64, unique=True, verbose_name='品牌名称')
    logo = models.ImageField(
        upload_to='brands/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Logo 文件',
    )
    logo_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='Logo 链接',
    )
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'products_brand'
        verbose_name = '品牌'
        verbose_name_plural = verbose_name
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

    @property
    def logo_display(self) -> str:
        """Return uploaded logo URL first, then external logo_url."""
        if self.logo:
            return self.logo.url
        if self.logo_url:
            return self.logo_url
        return ''


class Product(models.Model):
    """Product SKU."""

    STATUS_DRAFT = 'draft'
    STATUS_ON_SALE = 'on_sale'
    STATUS_OFF_SALE = 'off_sale'
    STATUS_CHOICES = [
        (STATUS_DRAFT, '草稿'),
        (STATUS_ON_SALE, '上架'),
        (STATUS_OFF_SALE, '下架'),
    ]

    name = models.CharField(max_length=128, verbose_name='商品名称')
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='分类',
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='品牌',
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='products',
        null=True,
        blank=True,
        verbose_name='商家',
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='售价')
    stock = models.PositiveIntegerField(default=0, verbose_name='库存')
    description = models.TextField(blank=True, default='', verbose_name='描述')
    image = models.ImageField(
        upload_to='products/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='主图',
    )
    gallery = models.JSONField(default=list, blank=True, verbose_name='轮播图')
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        verbose_name='状态',
    )
    is_active = models.BooleanField(default=True, verbose_name='是否有效')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    objects = TenantAwareManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'products_product'
        verbose_name = '商品'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self) -> str:
        return self.name


class InventoryLog(models.Model):
    """Product inventory change log."""

    TYPE_STOCK_IN = 'stock_in'
    TYPE_STOCK_OUT = 'stock_out'
    TYPE_TRANSFER = 'transfer'
    TYPE_GAIN = 'gain'
    TYPE_LOSS = 'loss'
    TYPE_ORDER_DEDUCT = 'order_deduct'
    TYPE_RETURN_IN = 'return_in'
    TYPE_CHOICES = [
        (TYPE_STOCK_IN, '入库'),
        (TYPE_STOCK_OUT, '出库'),
        (TYPE_TRANSFER, '调拨'),
        (TYPE_GAIN, '盘盈'),
        (TYPE_LOSS, '盘亏'),
        (TYPE_ORDER_DEDUCT, '订单扣减'),
        (TYPE_RETURN_IN, '退货入库'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory_logs',
        verbose_name='商品',
    )
    change_type = models.CharField(max_length=32, choices=TYPE_CHOICES, verbose_name='变动类型')
    before_quantity = models.IntegerField(verbose_name='变动前库存')
    after_quantity = models.IntegerField(verbose_name='变动后库存')
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='inventory_logs',
        verbose_name='操作人',
    )
    order = models.ForeignKey(
        'orders.Order',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='inventory_logs',
        verbose_name='关联订单',
    )
    remark = models.CharField(max_length=255, blank=True, default='', verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='变动时间')

    class Meta:
        db_table = 'products_inventory_log'
        verbose_name = '库存变动日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.product.name}-{self.get_change_type_display()}'
