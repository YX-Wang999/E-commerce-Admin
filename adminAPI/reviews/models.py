"""Product review models."""

from django.db import models


class ProductReview(models.Model):
    """Customer product review with social interactions."""

    STATUS_PUBLISHED = 'published'
    STATUS_HIDDEN = 'hidden'
    STATUS_DELETED = 'deleted'
    STATUS_CHOICES = [
        (STATUS_PUBLISHED, '已发布'),
        (STATUS_HIDDEN, '已隐藏'),
        (STATUS_DELETED, '已删除'),
    ]

    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='会员',
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='商品',
    )
    order = models.ForeignKey(
        'orders.Order',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviews',
        verbose_name='关联订单',
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='product_reviews',
        verbose_name='商家',
    )
    rating = models.PositiveSmallIntegerField(default=5, verbose_name='评分')
    content = models.TextField(max_length=500, verbose_name='评价内容')
    images = models.JSONField(default=list, blank=True, verbose_name='图片')
    video = models.URLField(blank=True, default='', verbose_name='视频')
    is_anonymous = models.BooleanField(default=False, verbose_name='匿名')
    allow_comment = models.BooleanField(default=True, verbose_name='允许评论')
    is_public = models.BooleanField(default=True, verbose_name='公开')
    view_count = models.PositiveIntegerField(default=0, verbose_name='浏览数')
    like_count = models.PositiveIntegerField(default=0, verbose_name='点赞数')
    comment_count = models.PositiveIntegerField(default=0, verbose_name='评论数')
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PUBLISHED,
        db_index=True,
        verbose_name='状态',
    )
    follow_up_content = models.TextField(blank=True, default='', verbose_name='追评内容')
    follow_up_images = models.JSONField(default=list, blank=True, verbose_name='追评图片')
    follow_up_video = models.URLField(blank=True, default='', verbose_name='追评视频')
    follow_up_at = models.DateTimeField(null=True, blank=True, verbose_name='追评时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'review_product_review'
        verbose_name = '商品评价'
        verbose_name_plural = verbose_name
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['customer', 'product', 'order'],
                condition=models.Q(order__isnull=False),
                name='uniq_review_customer_product_order',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.customer_id}-{self.product_id}'


class ReviewLike(models.Model):
    """Review like record."""

    review = models.ForeignKey(
        ProductReview,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='评价',
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='review_likes',
        verbose_name='会员',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'review_like'
        verbose_name = '评价点赞'
        verbose_name_plural = verbose_name
        unique_together = [('review', 'customer')]


class ReviewComment(models.Model):
    """Comment on a review."""

    review = models.ForeignKey(
        ProductReview,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='评价',
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='review_comments',
        verbose_name='会员',
    )
    content = models.CharField(max_length=500, verbose_name='评论内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'review_comment'
        verbose_name = '评价评论'
        verbose_name_plural = verbose_name
        ordering = ['id']
