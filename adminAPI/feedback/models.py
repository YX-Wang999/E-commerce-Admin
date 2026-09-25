"""Customer feedback models."""

from django.conf import settings
from django.db import models


class CustomerFeedback(models.Model):
    """Mall customer message / complaint / suggestion."""

    TYPE_COMPLAINT = 'complaint'
    TYPE_SUGGESTION = 'suggestion'
    TYPE_INQUIRY = 'inquiry'
    TYPE_AFTER_SALES = 'after_sales'
    TYPE_CHOICES = [
        (TYPE_COMPLAINT, '投诉'),
        (TYPE_SUGGESTION, '建议'),
        (TYPE_INQUIRY, '咨询'),
        (TYPE_AFTER_SALES, '售后'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_DONE = 'done'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待处理'),
        (STATUS_PROCESSING, '处理中'),
        (STATUS_DONE, '已处理'),
        (STATUS_CLOSED, '已关闭'),
    ]

    customer = models.ForeignKey(
        'customers.Customer',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='feedbacks',
        verbose_name='关联会员',
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        verbose_name='关联商户',
    )
    nickname = models.CharField(max_length=50, verbose_name='客户昵称')
    phone = models.CharField(max_length=20, verbose_name='联系方式')
    feedback_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name='留言类型',
    )
    content = models.TextField(max_length=500, verbose_name='留言内容')
    images = models.JSONField(default=list, blank=True, verbose_name='图片列表')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='状态',
    )
    handler = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='handled_feedbacks',
        verbose_name='处理人',
    )
    handler_remark = models.TextField(blank=True, default='', verbose_name='处理备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    handled_at = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')

    class Meta:
        db_table = 'feedback_customer_feedback'
        verbose_name = '客户留言'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self) -> str:
        return f'{self.nickname}-{self.feedback_type}'
