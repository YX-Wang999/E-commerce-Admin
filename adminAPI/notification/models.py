"""Unified notification model."""

from django.db import models


class Notification(models.Model):
    """In-app notification for staff, tenant, or customer."""

    RECIPIENT_CUSTOMER = 'customer'
    RECIPIENT_TENANT = 'tenant'
    RECIPIENT_STAFF = 'staff'
    RECIPIENT_CHOICES = [
        (RECIPIENT_CUSTOMER, '客户'),
        (RECIPIENT_TENANT, '商户'),
        (RECIPIENT_STAFF, '后台员工'),
    ]

    TYPE_ORDER = 'order'
    TYPE_REFUND = 'refund'
    TYPE_INVENTORY = 'inventory'
    TYPE_COMPLAINT = 'complaint'
    TYPE_TENANT = 'tenant'
    TYPE_CHAT = 'chat'
    TYPE_POINTS = 'points'
    TYPE_SYSTEM = 'system'
    TYPE_APPROVAL = 'approval'
    TYPE_ORDER_NEW = 'order_new'
    TYPE_ORDER_PAID = 'order_paid'
    TYPE_ORDER_SHIPPED = 'order_shipped'
    TYPE_ORDER_COMPLETED = 'order_completed'
    TYPE_ORDER_CANCELLED = 'order_cancelled'
    TYPE_REFUND_APPLIED = 'refund_applied'
    TYPE_REFUND_REVIEWED = 'refund_reviewed'
    TYPE_APPROVAL_PENDING = 'approval_pending'
    TYPE_APPROVAL_RESULT = 'approval_result'
    TYPE_SUBSIDY_APPLIED = 'subsidy_applied'
    TYPE_CLOSURE_APPLIED = 'closure_applied'
    TYPE_TENANT_APPLY = 'tenant_apply'
    TYPE_STOCK_WARNING = 'stock_warning'
    TYPE_CHOICES = [
        (TYPE_ORDER, '订单'),
        (TYPE_ORDER_NEW, '新订单'),
        (TYPE_ORDER_PAID, '订单已支付'),
        (TYPE_ORDER_SHIPPED, '订单已发货'),
        (TYPE_ORDER_COMPLETED, '订单已完成'),
        (TYPE_ORDER_CANCELLED, '订单已取消'),
        (TYPE_REFUND, '售后'),
        (TYPE_REFUND_APPLIED, '售后申请'),
        (TYPE_REFUND_REVIEWED, '售后审核'),
        (TYPE_INVENTORY, '库存'),
        (TYPE_STOCK_WARNING, '库存预警'),
        (TYPE_COMPLAINT, '投诉'),
        (TYPE_TENANT, '商户'),
        (TYPE_TENANT_APPLY, '入驻申请'),
        (TYPE_CHAT, '客服'),
        (TYPE_POINTS, '积分'),
        (TYPE_SYSTEM, '系统'),
        (TYPE_APPROVAL, '审核'),
        (TYPE_APPROVAL_PENDING, '待审核'),
        (TYPE_APPROVAL_RESULT, '审核结果'),
        (TYPE_SUBSIDY_APPLIED, '国补申请'),
        (TYPE_CLOSURE_APPLIED, '注销申请'),
    ]

    recipient_type = models.CharField(max_length=20, choices=RECIPIENT_CHOICES, db_index=True)
    recipient_id = models.PositiveIntegerField(db_index=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, db_index=True)
    related_url = models.CharField(max_length=500, blank=True, default='')
    related_id = models.PositiveIntegerField(null=True, blank=True)
    need_popup = models.BooleanField(default=False, verbose_name='需要弹窗')
    need_sound = models.BooleanField(default=False, verbose_name='需要声音')
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'notification'
        verbose_name = '通知'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient_type', 'recipient_id', 'is_read']),
        ]

    def __str__(self) -> str:
        return f'{self.get_recipient_type_display()}#{self.recipient_id}: {self.title}'
