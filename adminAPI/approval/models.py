"""Unified approval models."""

from django.conf import settings
from django.db import models


class Approval(models.Model):
    """Cross-module approval record."""

    TYPE_SUBSIDY = 'subsidy'
    TYPE_CLOSURE = 'closure'
    TYPE_TENANT_CHANGE = 'tenant_change'
    TYPE_PRODUCT = 'product'
    TYPE_COUPON = 'coupon'
    TYPE_SECKILL = 'seckill'
    TYPE_GROUPBUY = 'groupbuy'
    TYPE_REFUND = 'refund'
    TYPE_TAG = 'tag'
    TYPE_TENANT = 'tenant'
    TYPE_CHOICES = [
        (TYPE_SUBSIDY, '国补申请'),
        (TYPE_CLOSURE, '店铺注销'),
        (TYPE_TENANT_CHANGE, '商户信息变更'),
        (TYPE_PRODUCT, '商品审核'),
        (TYPE_COUPON, '优惠券审核'),
        (TYPE_SECKILL, '秒杀活动'),
        (TYPE_GROUPBUY, '团购活动'),
        (TYPE_REFUND, '退款审核'),
        (TYPE_TAG, '标签参与'),
        (TYPE_TENANT, '商户入驻'),
    ]

    APPLICANT_TENANT = 'tenant'
    APPLICANT_STAFF = 'staff'
    APPLICANT_CHOICES = [
        (APPLICANT_TENANT, '商户'),
        (APPLICANT_STAFF, '员工'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待审核'),
        (STATUS_APPROVED, '已通过'),
        (STATUS_REJECTED, '已驳回'),
        (STATUS_CANCELLED, '已取消'),
    ]

    PRIORITY_LOW = 'low'
    PRIORITY_NORMAL = 'normal'
    PRIORITY_HIGH = 'high'
    PRIORITY_URGENT = 'urgent'
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, '低'),
        (PRIORITY_NORMAL, '普通'),
        (PRIORITY_HIGH, '高'),
        (PRIORITY_URGENT, '紧急'),
    ]

    approval_type = models.CharField(max_length=50, choices=TYPE_CHOICES, db_index=True, verbose_name='审核类型')
    business_type = models.CharField(max_length=50, db_index=True, verbose_name='业务类型')
    business_id = models.PositiveIntegerField(db_index=True, verbose_name='业务ID')

    title = models.CharField(max_length=200, verbose_name='标题')
    summary = models.CharField(max_length=500, blank=True, default='', verbose_name='摘要')
    application_data = models.JSONField(default=dict, blank=True, verbose_name='申请数据')
    action_url = models.CharField(max_length=500, blank=True, default='', verbose_name='跳转链接')

    applicant_type = models.CharField(max_length=20, choices=APPLICANT_CHOICES, verbose_name='申请人类型')
    applicant_id = models.PositiveIntegerField(verbose_name='申请人ID')

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        verbose_name='状态',
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_approvals',
        verbose_name='审核人',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    reject_reason = models.TextField(blank=True, default='', verbose_name='驳回原因')
    review_remark = models.TextField(blank=True, default='', verbose_name='审核备注')

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_NORMAL,
        db_index=True,
        verbose_name='优先级',
    )
    timeout_at = models.DateTimeField(null=True, blank=True, verbose_name='超时时间')

    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'approval'
        verbose_name = '统一审核'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'approval_type']),
            models.Index(fields=['business_type', 'business_id']),
        ]

    def __str__(self) -> str:
        return f'{self.approval_type}#{self.business_id}:{self.status}'


class ApprovalLog(models.Model):
    """Approval action audit trail."""

    ACTION_SUBMIT = 'submit'
    ACTION_APPROVE = 'approve'
    ACTION_REJECT = 'reject'
    ACTION_CANCEL = 'cancel'
    ACTION_CHOICES = [
        (ACTION_SUBMIT, '提交'),
        (ACTION_APPROVE, '通过'),
        (ACTION_REJECT, '驳回'),
        (ACTION_CANCEL, '取消'),
    ]

    approval = models.ForeignKey(
        Approval,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='审核单',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='操作')
    operator_id = models.PositiveIntegerField(null=True, blank=True, verbose_name='操作人ID')
    operator_name = models.CharField(max_length=100, blank=True, default='', verbose_name='操作人')
    remark = models.TextField(blank=True, default='', verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')

    class Meta:
        db_table = 'approval_log'
        verbose_name = '审核日志'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self) -> str:
        return f'{self.approval_id}:{self.action}'
