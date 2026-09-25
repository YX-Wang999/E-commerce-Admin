"""Audit log models."""

from django.conf import settings
from django.db import models


class OperationLog(models.Model):
    """Record admin operations for auditing."""

    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_OTHER = 'other'
    ACTION_CHOICES = [
        (ACTION_CREATE, '新增'),
        (ACTION_UPDATE, '修改'),
        (ACTION_DELETE, '删除'),
        (ACTION_OTHER, '其他'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='operation_logs',
        verbose_name='操作用户',
    )
    username = models.CharField(max_length=150, blank=True, default='', verbose_name='用户名')
    module = models.CharField(max_length=64, verbose_name='模块')
    action = models.CharField(max_length=16, choices=ACTION_CHOICES, verbose_name='操作类型')
    resource = models.CharField(max_length=128, blank=True, default='', verbose_name='资源')
    resource_id = models.CharField(max_length=64, blank=True, default='', verbose_name='资源ID')
    detail = models.TextField(blank=True, default='', verbose_name='详情')
    ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP地址')
    user_agent = models.CharField(max_length=512, blank=True, default='', verbose_name='User-Agent')
    request_method = models.CharField(max_length=16, blank=True, default='', verbose_name='请求方法')
    request_path = models.CharField(max_length=512, blank=True, default='', verbose_name='请求路径')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')

    class Meta:
        db_table = 'audit_operation_log'
        verbose_name = '操作日志'
        verbose_name_plural = verbose_name
        ordering = ['-id']

    def __str__(self) -> str:
        return f'{self.username}-{self.module}-{self.action}'
