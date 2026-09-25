"""Promotional tag system models."""

from django.db import models


class TagCategory(models.Model):
    """Tag category (platform / tenant / product level)."""

    CATEGORY_PLATFORM = 'platform'
    CATEGORY_TENANT = 'tenant'
    CATEGORY_PRODUCT = 'product'
    CATEGORY_TYPES = [
        (CATEGORY_PLATFORM, '平台级标签'),
        (CATEGORY_TENANT, '商家级标签'),
        (CATEGORY_PRODUCT, '商品级标签'),
    ]

    name = models.CharField(max_length=50, verbose_name='分类名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='分类编码')
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES, verbose_name='分类类型')
    sort_order = models.IntegerField(default=0, verbose_name='排序')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'tag_system_category'
        verbose_name = '标签分类'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    """Tag definition."""

    name = models.CharField(max_length=50, verbose_name='标签名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='标签编码')
    category = models.ForeignKey(
        TagCategory,
        on_delete=models.CASCADE,
        related_name='tags',
        verbose_name='所属分类',
    )
    color = models.CharField(max_length=20, default='#FF6B35', verbose_name='背景色')
    text_color = models.CharField(max_length=20, default='#FFFFFF', verbose_name='文字色')
    icon = models.CharField(max_length=50, blank=True, default='', verbose_name='图标')
    priority = models.PositiveSmallIntegerField(default=50, verbose_name='优先级')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    can_tenant_use = models.BooleanField(default=True, verbose_name='商家可使用')
    can_product_use = models.BooleanField(default=True, verbose_name='商品可打标')
    requires_approval = models.BooleanField(default=False, verbose_name='需要审核')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'tag_system_tag'
        verbose_name = '促销标签'
        verbose_name_plural = verbose_name
        ordering = ['-priority', 'id']

    def __str__(self) -> str:
        return self.name


class TenantTagConfig(models.Model):
    """Tenant participation in a tag activity."""

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
        related_name='tag_configs',
        verbose_name='商家',
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='tenant_configs',
        verbose_name='标签',
    )
    is_participating = models.BooleanField(default=False, verbose_name='是否参与')
    custom_name = models.CharField(max_length=50, blank=True, default='', verbose_name='自定义名称')
    rules = models.JSONField(default=dict, blank=True, verbose_name='规则')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_APPROVED,
        verbose_name='审核状态',
    )
    reject_reason = models.TextField(blank=True, default='', verbose_name='驳回原因')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'tag_system_tenant_config'
        verbose_name = '商家标签配置'
        verbose_name_plural = verbose_name
        unique_together = [('tenant', 'tag')]

    def __str__(self) -> str:
        return f'{self.tenant_id}:{self.tag.code}'


class ProductTagConfig(models.Model):
    """Product-level tag assignment."""

    SOURCE_PLATFORM = 'platform'
    SOURCE_TENANT = 'tenant'
    SOURCE_AUTO = 'auto'
    SOURCE_CHOICES = [
        (SOURCE_PLATFORM, '平台'),
        (SOURCE_TENANT, '商家'),
        (SOURCE_AUTO, '系统自动'),
    ]

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='tag_configs',
        verbose_name='商品',
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='product_configs',
        verbose_name='标签',
    )
    is_active = models.BooleanField(default=False, verbose_name='是否打标')
    display_text = models.CharField(max_length=50, blank=True, default='', verbose_name='展示文案')
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default=SOURCE_TENANT,
        verbose_name='来源',
    )
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'tag_system_product_config'
        verbose_name = '商品标签配置'
        verbose_name_plural = verbose_name
        unique_together = [('product', 'tag')]

    def __str__(self) -> str:
        return f'{self.product_id}:{self.tag.code}'
