"""Customer service chat models."""

from django.conf import settings
from django.db import models

from common.tenant import TenantAwareManager


class Complaint(models.Model):
    """Customer complaint against a merchant (dispute workflow)."""

    CATEGORY_PRODUCT_QUALITY = 'product_quality'
    CATEGORY_SHIPPING = 'shipping'
    CATEGORY_SERVICE = 'service'
    CATEGORY_FRAUD = 'fraud'
    CATEGORY_REFUND = 'refund'
    CATEGORY_OTHER = 'other'
    CATEGORY_CHOICES = [
        (CATEGORY_PRODUCT_QUALITY, '商品质量问题'),
        (CATEGORY_SHIPPING, '物流问题'),
        (CATEGORY_SERVICE, '服务态度'),
        (CATEGORY_FRAUD, '欺诈/虚假宣传'),
        (CATEGORY_REFUND, '退款纠纷'),
        (CATEGORY_OTHER, '其他'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_MERCHANT_PROCESSING = 'merchant_processing'
    STATUS_CUSTOMER_REVIEW = 'customer_review'
    STATUS_PLATFORM_REVIEWING = 'platform_reviewing'
    STATUS_RESOLVED = 'resolved'
    STATUS_REJECTED = 'rejected'
    STATUS_CLOSED = 'closed'
    # Legacy alias kept for migration compatibility
    STATUS_REVIEWING = 'reviewing'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待处理'),
        (STATUS_MERCHANT_PROCESSING, '商户处理中'),
        (STATUS_CUSTOMER_REVIEW, '用户确认中'),
        (STATUS_PLATFORM_REVIEWING, '平台仲裁中'),
        (STATUS_RESOLVED, '已解决'),
        (STATUS_REJECTED, '已驳回'),
        (STATUS_CLOSED, '已关闭'),
    ]

    DECISION_REFUND = 'refund'
    DECISION_PARTIAL_REFUND = 'partial_refund'
    DECISION_COMPENSATION = 'compensation'
    DECISION_DISMISS = 'dismiss'
    DECISION_CHOICES = [
        (DECISION_REFUND, '退款'),
        (DECISION_PARTIAL_REFUND, '部分退款'),
        (DECISION_COMPENSATION, '补偿'),
        (DECISION_DISMISS, '驳回'),
    ]

    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='complaints',
        verbose_name='客户',
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='complaints',
        verbose_name='被投诉商户',
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='complaints',
        verbose_name='关联订单',
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name='投诉类型')
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='投诉内容')
    attachments = models.JSONField(default=list, blank=True, verbose_name='附件')
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='状态',
    )
    merchant_reply = models.TextField(blank=True, default='', verbose_name='商户回复摘要')
    merchant_replied_at = models.DateTimeField(null=True, blank=True, verbose_name='商户回复时间')
    customer_satisfied = models.BooleanField(null=True, blank=True, verbose_name='用户是否满意')
    customer_reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='用户确认时间')
    platform_decision = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
        blank=True,
        default='',
        verbose_name='平台裁决',
    )
    platform_remark = models.TextField(blank=True, default='', verbose_name='平台仲裁说明')
    platform_reply = models.TextField(blank=True, default='', verbose_name='平台回复')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_complaints',
        verbose_name='平台处理人',
    )
    platform_reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='平台仲裁时间')
    resolution = models.TextField(blank=True, default='', verbose_name='处理结果')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='解决时间')

    class Meta:
        db_table = 'chat_complaint'
        verbose_name = '商户投诉'
        verbose_name_plural = '商户投诉'
        ordering = ['-id']

    def __str__(self) -> str:
        return f'{self.complaint_no}:{self.category}'

    @property
    def complaint_no(self) -> str:
        created = self.created_at.strftime('%Y%m%d') if self.created_at else '00000000'
        return f'CPL{created}{self.pk:04d}'


class ComplaintMessage(models.Model):
    """Multi-turn messages on a complaint dispute."""

    SENDER_CUSTOMER = 'customer'
    SENDER_MERCHANT = 'merchant'
    SENDER_PLATFORM = 'platform'
    SENDER_TYPE_CHOICES = [
        (SENDER_CUSTOMER, '用户'),
        (SENDER_MERCHANT, '商户'),
        (SENDER_PLATFORM, '平台'),
    ]

    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='投诉',
    )
    sender_type = models.CharField(max_length=20, choices=SENDER_TYPE_CHOICES, verbose_name='发送方')
    sender_id = models.PositiveIntegerField(verbose_name='发送者ID')
    content = models.TextField(verbose_name='内容')
    attachments = models.JSONField(default=list, blank=True, verbose_name='附件')
    is_internal = models.BooleanField(default=False, verbose_name='平台内部备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='发送时间')

    class Meta:
        db_table = 'chat_complaint_message'
        verbose_name = '投诉消息'
        verbose_name_plural = '投诉消息'
        ordering = ['created_at']

    def __str__(self) -> str:
        preview = (self.content or '')[:40]
        return f'{self.sender_type}#{self.sender_id}: {preview}'


class Conversation(models.Model):
    """Chat session between participants (customer / merchant / platform)."""

    TYPE_B2C = 'b2c'
    TYPE_C2P = 'c2p'
    TYPE_B2P = 'b2p'
    TYPE_P2B = 'p2b'
    TYPE_C2P_B = 'c2p_b'
    TYPE_CHOICES = [
        (TYPE_B2C, '商户→客户'),
        (TYPE_C2P, '客户→平台'),
        (TYPE_B2P, '商户→平台'),
        (TYPE_P2B, '平台→商户'),
        (TYPE_C2P_B, '客户投诉商户'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待分配'),
        (STATUS_ACTIVE, '进行中'),
        (STATUS_CLOSED, '已关闭'),
    ]

    conversation_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_C2P,
        verbose_name='会话类型',
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='conversations',
        null=True,
        blank=True,
        verbose_name='所属商家',
    )
    user = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='conversations',
        null=True,
        blank=True,
        verbose_name='商城用户',
    )
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        verbose_name='关联投诉',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_conversations',
        verbose_name='负责客服',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='状态',
    )
    unread_count_user = models.PositiveIntegerField(default=0, verbose_name='用户端未读')
    unread_count_staff = models.PositiveIntegerField(default=0, verbose_name='客服端未读')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    objects = TenantAwareManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ['-updated_at']
        verbose_name = '客服会话'
        verbose_name_plural = '客服会话'

    def __str__(self) -> str:
        tenant_name = self.tenant.name if self.tenant_id else '平台'
        return f'{self.get_conversation_type_display()} {tenant_name} #{self.pk}'

    @property
    def customer(self):
        return self.user

    @property
    def is_merchant_conversation(self) -> bool:
        return self.conversation_type in {self.TYPE_B2P, self.TYPE_P2B}


class Message(models.Model):
    """Persisted chat message."""

    SENDER_USER = 'user'
    SENDER_STAFF = 'staff'
    SENDER_SYSTEM = 'system'
    SENDER_TYPE_CHOICES = [
        (SENDER_USER, '用户'),
        (SENDER_STAFF, '客服'),
        (SENDER_SYSTEM, '系统'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='会话',
    )
    sender_type = models.CharField(
        max_length=10,
        choices=SENDER_TYPE_CHOICES,
        default=SENDER_USER,
        verbose_name='发送者类型',
    )
    sender_user = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sent_messages',
        verbose_name='用户发送者',
    )
    sender_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sent_messages',
        verbose_name='客服发送者',
    )
    content = models.TextField(verbose_name='内容')
    is_sensitive = models.BooleanField(default=False, verbose_name='是否敏感信息')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='已读时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='发送时间')

    class Meta:
        ordering = ['created_at']
        verbose_name = '聊天消息'
        verbose_name_plural = '聊天消息'

    def __str__(self) -> str:
        preview = (self.content or '')[:30]
        return f'{self.sender_type}: {preview}...'

    @property
    def is_staff(self) -> bool:
        return self.sender_type == self.SENDER_STAFF


class StaffPresence(models.Model):
    """Online status for support staff."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_presence',
        verbose_name='客服',
    )
    is_online = models.BooleanField(default=False, verbose_name='是否在线')
    last_seen = models.DateTimeField(auto_now=True, verbose_name='最后活跃')

    class Meta:
        verbose_name = '客服在线状态'
        verbose_name_plural = '客服在线状态'

    def __str__(self) -> str:
        return f'{self.user_id} online={self.is_online}'
