"""Customer models."""

from django.contrib.auth.hashers import check_password, make_password
from django.db import models

from common.tenant import TenantAwareManager


class Customer(models.Model):
    """Mall customer account (independent from admin User)."""

    LEVEL_NORMAL = 'normal'
    LEVEL_SILVER = 'silver'
    LEVEL_GOLD = 'gold'
    LEVEL_PLATINUM = 'platinum'
    LEVEL_DIAMOND = 'diamond'
    LEVEL_CHOICES = [
        (LEVEL_NORMAL, '普通会员'),
        (LEVEL_SILVER, '白银会员'),
        (LEVEL_GOLD, '黄金会员'),
        (LEVEL_PLATINUM, '铂金会员'),
        (LEVEL_DIAMOND, '钻石会员'),
    ]

    phone = models.CharField(max_length=32, verbose_name='手机号')
    password = models.CharField(max_length=128, verbose_name='密码')
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='customers',
        null=True,
        blank=True,
        verbose_name='商家',
    )
    email = models.EmailField(max_length=128, blank=True, default='', verbose_name='邮箱')
    nickname = models.CharField(max_length=64, blank=True, default='', verbose_name='昵称')
    name = models.CharField(max_length=64, verbose_name='姓名')
    avatar = models.URLField(max_length=512, blank=True, default='', verbose_name='头像')
    real_name = models.CharField(max_length=64, blank=True, default='', verbose_name='真实姓名')
    level = models.CharField(
        max_length=16,
        choices=LEVEL_CHOICES,
        default=LEVEL_NORMAL,
        verbose_name='会员等级',
    )
    points = models.PositiveIntegerField(default=0, verbose_name='积分')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='注册时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    objects = TenantAwareManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'customers_customer'
        verbose_name = '商城用户'
        verbose_name_plural = verbose_name
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'phone'],
                name='customers_customer_tenant_phone_uniq',
            ),
        ]

    def __str__(self) -> str:
        return self.display_name

    @property
    def display_name(self) -> str:
        return self.nickname or self.name or self.phone

    def set_password(self, raw_password: str) -> None:
        self.password = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        if self.nickname and not self.name:
            self.name = self.nickname
        elif self.name and not self.nickname:
            self.nickname = self.name
        super().save(*args, **kwargs)


class SmsVerificationCode(models.Model):
    """SMS verification code for register / reset password."""

    SCENE_REGISTER = 'register'
    SCENE_RESET_PASSWORD = 'reset_password'
    SCENE_LOGIN = 'login'
    SCENE_CHOICES = [
        (SCENE_REGISTER, '注册'),
        (SCENE_RESET_PASSWORD, '找回密码'),
        (SCENE_LOGIN, '登录'),
    ]

    phone = models.CharField(max_length=32, verbose_name='手机号')
    code = models.CharField(max_length=8, verbose_name='验证码')
    scene = models.CharField(max_length=32, choices=SCENE_CHOICES, verbose_name='场景')
    out_id = models.CharField(max_length=64, blank=True, default='', verbose_name='阿里云OutId')
    expires_at = models.DateTimeField(verbose_name='过期时间')
    is_used = models.BooleanField(default=False, verbose_name='是否已使用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'customers_sms_code'
        verbose_name = '短信验证码'
        verbose_name_plural = verbose_name
        ordering = ['-id']
        indexes = [
            models.Index(fields=['phone', 'scene', '-created_at']),
        ]

    def __str__(self) -> str:
        return f'{self.phone}:{self.scene}'
