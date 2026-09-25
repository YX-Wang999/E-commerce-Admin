"""Tenant models."""

from django.conf import settings
from django.db import models
from django.utils import timezone


class Tenant(models.Model):
    """租户/商家."""

    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_SUSPENDED = 'suspended'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待审核'),
        (STATUS_ACTIVE, '已入驻'),
        (STATUS_SUSPENDED, '已暂停'),
        (STATUS_CLOSED, '已关闭'),
    ]

    name = models.CharField(max_length=100, verbose_name='商家名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='商家编码')
    logo = models.URLField(max_length=200, blank=True, null=True, verbose_name='Logo')
    contact_name = models.CharField(max_length=50, verbose_name='联系人')
    contact_phone = models.CharField(max_length=20, unique=True, verbose_name='联系电话')
    contact_email = models.EmailField(verbose_name='联系邮箱')
    legal_person = models.CharField(max_length=50, blank=True, default='', verbose_name='法人姓名')
    business_license = models.URLField(max_length=500, blank=True, default='', verbose_name='营业执照')
    address = models.TextField(blank=True, null=True, verbose_name='商家地址')
    description = models.TextField(blank=True, default='', verbose_name='店铺描述')
    pending_name = models.CharField(max_length=100, blank=True, default='', verbose_name='待审核名称')
    pending_contact_phone = models.CharField(max_length=20, blank=True, default='', verbose_name='待审核电话')
    pending_contact_email = models.EmailField(blank=True, default='', verbose_name='待审核邮箱')
    pending_contact_name = models.CharField(max_length=50, blank=True, default='', verbose_name='待审核联系人')
    pending_legal_person = models.CharField(max_length=50, blank=True, default='', verbose_name='待审核法人')
    pending_business_license = models.URLField(max_length=500, blank=True, default='', verbose_name='待审核执照')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='入驻状态',
    )
    applied_at = models.DateTimeField(auto_now_add=True, verbose_name='申请时间')
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_tenants',
        verbose_name='审核人',
    )
    config = models.JSONField(default=dict, blank=True, verbose_name='商家配置')
    department = models.ForeignKey(
        'accounts.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenants',
        verbose_name='对接部门',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    class Meta:
        db_table = 'tenants_tenant'
        verbose_name = '商家'
        verbose_name_plural = '商家管理'
        ordering = ['-id']

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            from tenants.utils import generate_store_code

            self.code = generate_store_code()
        if self.status == self.STATUS_ACTIVE and not self.approved_at:
            self.approved_at = timezone.now()
        super().save(*args, **kwargs)


class TenantStaff(models.Model):
    """商家员工（商家管理员 + 员工）."""

    ROLE_OWNER = 'owner'
    ROLE_MANAGER = 'manager'
    ROLE_STAFF = 'staff'
    ROLE_CHOICES = [
        (ROLE_OWNER, '商家管理员'),
        (ROLE_MANAGER, '经理'),
        (ROLE_STAFF, '普通员工'),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='staffs',
        verbose_name='商家',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tenant_staffs',
        verbose_name='用户',
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STAFF,
        verbose_name='员工角色',
    )
    permissions = models.JSONField(default=list, blank=True, verbose_name='自定义权限')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'tenants_staff'
        verbose_name = '商家员工'
        verbose_name_plural = '商家员工'
        unique_together = [('tenant', 'user')]

    def __str__(self) -> str:
        return f'{self.tenant.code}:{self.user_id}'


class TenantActionLog(models.Model):
    """Tenant status change audit trail."""

    ACTION_APPROVE = 'approve'
    ACTION_SUSPEND = 'suspend'
    ACTION_RESUME = 'resume'
    ACTION_CREATE = 'create'
    ACTION_DELETE = 'delete'
    ACTION_CLOSE = 'close'
    ACTION_CHOICES = [
        (ACTION_APPROVE, '审核通过'),
        (ACTION_SUSPEND, '暂停商户'),
        (ACTION_RESUME, '恢复商户'),
        (ACTION_CREATE, '创建商户'),
        (ACTION_DELETE, '删除商户'),
        (ACTION_CLOSE, '关闭商户'),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='action_logs',
        verbose_name='商家',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='操作类型')
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenant_action_logs',
        verbose_name='操作人',
    )
    remark = models.CharField(max_length=255, blank=True, default='', verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')

    class Meta:
        db_table = 'tenants_action_log'
        verbose_name = '商户操作记录'
        verbose_name_plural = '商户操作记录'
        ordering = ['-id']

    def __str__(self) -> str:
        return f'{self.tenant_id}:{self.action}'


class TenantSuspensionLog(models.Model):
    """商户暂停/恢复/关闭记录."""

    ACTION_SUSPEND = 'suspend'
    ACTION_RESTORE = 'restore'
    ACTION_CLOSE = 'close'
    ACTION_CHOICES = [
        (ACTION_SUSPEND, '暂停'),
        (ACTION_RESTORE, '恢复'),
        (ACTION_CLOSE, '关闭'),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='suspension_logs',
        verbose_name='商家',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='操作')
    reason = models.TextField(verbose_name='原因')
    detail = models.JSONField(default=dict, blank=True, verbose_name='详细信息')
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenant_suspension_logs',
        verbose_name='操作人',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')

    class Meta:
        db_table = 'tenants_suspension_log'
        verbose_name = '商户状态记录'
        verbose_name_plural = '商户状态记录'
        ordering = ['-id']

    def __str__(self) -> str:
        return f'{self.tenant_id}:{self.action}'


class TenantAppeal(models.Model):
    """商户申诉."""

    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_RESOLVED = 'resolved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待处理'),
        (STATUS_PROCESSING, '处理中'),
        (STATUS_RESOLVED, '已解决'),
        (STATUS_REJECTED, '已驳回'),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='appeals',
        verbose_name='商家',
    )
    title = models.CharField(max_length=200, verbose_name='申诉标题')
    content = models.TextField(verbose_name='申诉内容')
    attachments = models.JSONField(default=list, blank=True, verbose_name='附件')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='状态',
    )
    reply = models.TextField(blank=True, default='', verbose_name='平台回复')
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='handled_tenant_appeals',
        verbose_name='处理人',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'tenants_appeal'
        verbose_name = '商户申诉'
        verbose_name_plural = '商户申诉'
        ordering = ['-id']

    def __str__(self) -> str:
        return f'{self.tenant_id}:{self.title}'


class TenantAppealMessage(models.Model):
    """Threaded appeal messages between merchant and platform."""

    SENDER_PLATFORM = 'platform'
    SENDER_MERCHANT = 'merchant'
    SENDER_CHOICES = [
        (SENDER_PLATFORM, '平台'),
        (SENDER_MERCHANT, '商户'),
    ]

    appeal = models.ForeignKey(
        TenantAppeal,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='申诉',
    )
    sender_type = models.CharField(max_length=20, choices=SENDER_CHOICES, verbose_name='发送方')
    sender_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenant_appeal_messages',
        verbose_name='发送人',
    )
    content = models.TextField(verbose_name='内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='发送时间')

    class Meta:
        db_table = 'tenants_appeal_message'
        ordering = ['created_at']
        verbose_name = '申诉消息'
        verbose_name_plural = '申诉消息'


class TenantInboxMessage(models.Model):
    """In-app inbox for tenant staff (appeal replies, system notices)."""

    TYPE_APPEAL_REPLY = 'appeal_reply'
    TYPE_SYSTEM = 'system'
    TYPE_CHOICES = [
        (TYPE_APPEAL_REPLY, '申诉回复'),
        (TYPE_SYSTEM, '系统通知'),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='inbox_messages',
        verbose_name='商家',
    )
    appeal = models.ForeignKey(
        TenantAppeal,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='inbox_messages',
        verbose_name='关联申诉',
    )
    message_type = models.CharField(max_length=32, choices=TYPE_CHOICES, verbose_name='类型')
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    is_read = models.BooleanField(default=False, verbose_name='已读')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'tenants_inbox_message'
        ordering = ['-created_at']
        verbose_name = '商户站内信'
        verbose_name_plural = '商户站内信'


class TenantChangeLog(models.Model):
    """Merchant profile change audit trail."""

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待审核'),
        (STATUS_APPROVED, '已通过'),
        (STATUS_REJECTED, '已驳回'),
    ]

    OPERATOR_TENANT = 'tenant'
    OPERATOR_PLATFORM = 'platform'
    OPERATOR_TYPE_CHOICES = [
        (OPERATOR_TENANT, '商户'),
        (OPERATOR_PLATFORM, '平台'),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='change_logs',
        verbose_name='商家',
    )
    field = models.CharField(max_length=50, verbose_name='变更字段')
    old_value = models.TextField(blank=True, default='', verbose_name='原值')
    new_value = models.TextField(blank=True, default='', verbose_name='新值')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        verbose_name='审核状态',
    )
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenant_change_logs',
        verbose_name='提交人',
    )
    operator_type = models.CharField(
        max_length=20,
        choices=OPERATOR_TYPE_CHOICES,
        default=OPERATOR_TENANT,
        verbose_name='操作方',
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_tenant_changes',
        verbose_name='审核人',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    review_remark = models.CharField(max_length=500, blank=True, default='', verbose_name='审核备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='提交时间')

    class Meta:
        db_table = 'tenants_change_log'
        ordering = ['-id']
        verbose_name = '商户变更记录'
        verbose_name_plural = '商户变更记录'
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self) -> str:
        return f'{self.tenant_id}:{self.field}:{self.status}'
