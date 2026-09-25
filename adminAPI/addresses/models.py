"""Shipping address models."""

from django.db import models

from common.tenant import TenantAwareManager


class Address(models.Model):
    """Customer shipping address."""

    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name='商城用户',
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='addresses',
        null=True,
        blank=True,
        verbose_name='商家',
    )
    name = models.CharField(max_length=64, verbose_name='收件人')
    phone = models.CharField(max_length=20, verbose_name='手机号')
    province = models.CharField(max_length=64, verbose_name='省')
    city = models.CharField(max_length=64, verbose_name='市')
    district = models.CharField(max_length=64, verbose_name='区')
    detail = models.CharField(max_length=255, verbose_name='详细地址')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    objects = TenantAwareManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'addresses_address'
        verbose_name = '收货地址'
        verbose_name_plural = verbose_name
        ordering = ['-is_default', '-id']

    def __str__(self) -> str:
        return f'{self.name} {self.phone}'

    @property
    def full_address(self) -> str:
        return f'{self.province}{self.city}{self.district}{self.detail}'
