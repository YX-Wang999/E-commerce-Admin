"""System announcement models."""

from django.conf import settings
from django.db import models


class Announcement(models.Model):
    """System-wide announcement for admin users."""

    TYPE_MAINTENANCE = 'maintenance'
    TYPE_UPDATE = 'update'
    TYPE_NOTICE = 'notice'
    TYPE_DAILY = 'daily'
    TYPE_CHOICES = [
        (TYPE_MAINTENANCE, '系统维护'),
        (TYPE_UPDATE, '功能更新'),
        (TYPE_NOTICE, '重要通知'),
        (TYPE_DAILY, '日常公告'),
    ]

    PRIORITY_NORMAL = 'normal'
    PRIORITY_IMPORTANT = 'important'
    PRIORITY_URGENT = 'urgent'
    PRIORITY_CHOICES = [
        (PRIORITY_NORMAL, '普通'),
        (PRIORITY_IMPORTANT, '重要'),
        (PRIORITY_URGENT, '紧急'),
    ]

    SCOPE_ALL = 'all'
    SCOPE_ROLE = 'role'
    SCOPE_DEPARTMENT = 'department'
    SCOPE_CHOICES = [
        (SCOPE_ALL, '全部用户'),
        (SCOPE_ROLE, '指定角色'),
        (SCOPE_DEPARTMENT, '指定部门'),
    ]

    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_OFFLINE = 'offline'
    STATUS_CHOICES = [
        (STATUS_DRAFT, '草稿'),
        (STATUS_PUBLISHED, '已发布'),
        (STATUS_OFFLINE, '已下线'),
    ]

    title = models.CharField(max_length=100, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    announce_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name='公告类型',
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_NORMAL,
        verbose_name='优先级',
    )
    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default=SCOPE_ALL,
        verbose_name='发布范围',
    )
    target_roles = models.ManyToManyField(
        'rbac.Role',
        blank=True,
        related_name='announcements',
        verbose_name='目标角色',
    )
    target_departments = models.ManyToManyField(
        'accounts.Department',
        blank=True,
        related_name='announcements',
        verbose_name='目标部门',
    )
    is_pinned = models.BooleanField(default=False, verbose_name='是否置顶')
    effective_at = models.DateTimeField(verbose_name='生效时间')
    expires_at = models.DateTimeField(verbose_name='失效时间')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        verbose_name='状态',
    )
    publisher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='published_announcements',
        verbose_name='发布人',
    )
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='发布时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'announcement_announcement'
        verbose_name = '系统公告'
        verbose_name_plural = verbose_name
        ordering = ['-is_pinned', '-published_at', '-id']

    def __str__(self) -> str:
        return self.title
