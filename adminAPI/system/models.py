"""System configuration models."""

from django.db import models


class SystemSetting(models.Model):
    """Key-value system settings."""

    VALUE_TYPE_STRING = 'string'
    VALUE_TYPE_NUMBER = 'number'
    VALUE_TYPE_BOOLEAN = 'boolean'
    VALUE_TYPE_FILE = 'file'
    VALUE_TYPE_CHOICES = [
        (VALUE_TYPE_STRING, '字符串'),
        (VALUE_TYPE_NUMBER, '数字'),
        (VALUE_TYPE_BOOLEAN, '布尔'),
        (VALUE_TYPE_FILE, '文件'),
    ]

    key = models.CharField(max_length=128, unique=True, verbose_name='配置键')
    value = models.TextField(blank=True, default='', verbose_name='配置值')
    value_type = models.CharField(
        max_length=16,
        choices=VALUE_TYPE_CHOICES,
        default=VALUE_TYPE_STRING,
        verbose_name='值类型',
    )
    description = models.CharField(max_length=255, blank=True, default='', verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'system_setting'
        verbose_name = '系统配置'
        verbose_name_plural = verbose_name
        ordering = ['key']

    def __str__(self) -> str:
        return self.key
