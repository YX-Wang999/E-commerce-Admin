"""Shop closure models."""

from django.conf import settings
from django.db import models


class ClosureApplication(models.Model):
    """Merchant shop closure application."""

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_NOTICE_PERIOD = 'notice_period'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待审核'),
        (STATUS_APPROVED, '审核通过'),
        (STATUS_REJECTED, '审核驳回'),
        (STATUS_NOTICE_PERIOD, '公示期'),
        (STATUS_COMPLETED, '已注销'),
        (STATUS_CANCELLED, '已取消'),
    ]

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='closure_applications',
        verbose_name='商家',
    )
    reason = models.CharField(max_length=200, verbose_name='注销原因')
    detail = models.TextField(blank=True, default='', verbose_name='详细说明')
    attachments = models.JSONField(default=list, blank=True, verbose_name='附件')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name='状态')

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_closure_applications',
        verbose_name='审核人',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    reject_reason = models.TextField(blank=True, default='', verbose_name='驳回原因')

    notice_start_at = models.DateTimeField(null=True, blank=True, verbose_name='公示开始时间')
    notice_end_at = models.DateTimeField(null=True, blank=True, verbose_name='公示结束时间')
    notice_days = models.PositiveIntegerField(default=15, verbose_name='公示天数')

    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='注销完成时间')
    data_exported_at = models.DateTimeField(null=True, blank=True, verbose_name='数据导出时间')
    data_export_url = models.URLField(max_length=500, blank=True, default='', verbose_name='数据下载链接')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='申请时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'shop_closure_application'
        verbose_name = '店铺注销申请'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self) -> str:
        return f'{self.tenant_id}:{self.status}'


class ClosureChecklist(models.Model):
    """Closure precondition checklist item."""

    application = models.ForeignKey(
        ClosureApplication,
        on_delete=models.CASCADE,
        related_name='checklist',
        verbose_name='申请',
    )
    item = models.CharField(max_length=100, verbose_name='检查项')
    code = models.CharField(max_length=50, verbose_name='检查编码')
    is_completed = models.BooleanField(default=False, verbose_name='是否完成')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    remark = models.TextField(blank=True, default='', verbose_name='备注')

    class Meta:
        db_table = 'shop_closure_checklist'
        verbose_name = '注销检查清单'
        verbose_name_plural = verbose_name
        unique_together = [('application', 'code')]

    def __str__(self) -> str:
        return f'{self.application_id}:{self.code}'


class ClosureNotification(models.Model):
    """Closure notification log."""

    CHANNEL_EMAIL = 'email'
    CHANNEL_SMS = 'sms'
    CHANNEL_IN_APP = 'in_app'
    CHANNEL_CHOICES = [
        (CHANNEL_EMAIL, '邮件'),
        (CHANNEL_SMS, '短信'),
        (CHANNEL_IN_APP, '站内信'),
    ]

    application = models.ForeignKey(
        ClosureApplication,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='申请',
    )
    recipient = models.CharField(max_length=200, verbose_name='接收方')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, verbose_name='渠道')
    content = models.TextField(verbose_name='内容')
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name='发送时间')
    is_delivered = models.BooleanField(default=False, verbose_name='是否送达')

    class Meta:
        db_table = 'shop_closure_notification'
        verbose_name = '注销通知'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self) -> str:
        return f'{self.application_id}:{self.channel}'
