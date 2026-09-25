"""User models."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class Department(models.Model):
    """Organizational department."""

    name = models.CharField(max_length=64, verbose_name='部门名称')
    code = models.CharField(max_length=32, unique=True, verbose_name='部门编码')
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
        verbose_name='上级部门',
    )
    manager = models.ForeignKey(
        'User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='managed_departments',
        verbose_name='部门经理',
    )
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'accounts_department'
        verbose_name = '部门'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    """Admin user model."""

    nickname = models.CharField(max_length=64, blank=True, default='', verbose_name='昵称')
    avatar = models.URLField(max_length=512, blank=True, default='', verbose_name='头像')
    phone = models.CharField(max_length=20, blank=True, default='', verbose_name='手机号')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    is_first_login = models.BooleanField(default=True, verbose_name='是否首次登录')
    activation_token = models.CharField(
        max_length=512,
        blank=True,
        default='',
        verbose_name='激活令牌',
    )
    token_created_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='激活令牌创建时间',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='members',
        verbose_name='所属部门',
    )
    supervisor = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='subordinates',
        verbose_name='直属上级',
    )
    roles = models.ManyToManyField(
        'rbac.Role',
        blank=True,
        related_name='users',
        verbose_name='角色',
    )

    @property
    def managed_department(self) -> Department | None:
        """Primary department this user manages (via Department.manager)."""
        return self.managed_departments.filter(is_active=True).first()

    class Meta:
        db_table = 'accounts_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self) -> str:
        return self.username


class ActivationLog(models.Model):
    """Track account activation email delivery and status."""

    STATUS_PENDING = 'pending'
    STATUS_EXPIRED = 'expired'
    STATUS_ACTIVATED = 'activated'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待激活'),
        (STATUS_EXPIRED, '已过期'),
        (STATUS_ACTIVATED, '已激活'),
        (STATUS_FAILED, '发送失败'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activation_logs',
        verbose_name='用户',
    )
    token = models.CharField(max_length=255, verbose_name='激活令牌')
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name='邮件发送时间')
    activated_at = models.DateTimeField(null=True, blank=True, verbose_name='实际激活时间')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='状态',
    )
    expired_at = models.DateTimeField(verbose_name='令牌过期时间')

    class Meta:
        db_table = 'accounts_activation_log'
        verbose_name = '激活记录'
        verbose_name_plural = verbose_name
        ordering = ['-sent_at']

    def __str__(self) -> str:
        return f'{self.user.username}-{self.status}'
