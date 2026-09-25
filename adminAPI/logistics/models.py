"""Logistics models."""

from django.db import models


class Logistics(models.Model):
    """Shipment and tracking for an order."""

    STATUS_PENDING = 'pending'
    STATUS_PICKED = 'picked'
    STATUS_TRANSPORTING = 'transporting'
    STATUS_DELIVERING = 'delivering'
    STATUS_DELIVERED = 'delivered'
    STATUS_EXCEPTION = 'exception'
    STATUS_RETURNED = 'returned'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待发货'),
        (STATUS_PICKED, '已揽收'),
        (STATUS_TRANSPORTING, '运输中'),
        (STATUS_DELIVERING, '派送中'),
        (STATUS_DELIVERED, '已签收'),
        (STATUS_EXCEPTION, '异常'),
        (STATUS_RETURNED, '已退回'),
    ]

    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='logistics',
        verbose_name='订单',
    )
    express_company = models.CharField(max_length=50, verbose_name='快递公司')
    express_code = models.CharField(max_length=20, verbose_name='快递公司编码')
    tracking_number = models.CharField(max_length=100, verbose_name='物流单号')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='物流状态',
    )
    traces = models.JSONField(default=list, blank=True, verbose_name='轨迹')
    raw_response = models.JSONField(default=dict, blank=True, verbose_name='原始响应')
    picked_at = models.DateTimeField(null=True, blank=True, verbose_name='揽收时间')
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='签收时间')
    last_trace_at = models.DateTimeField(null=True, blank=True, verbose_name='最后轨迹时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'logistics_logistics'
        verbose_name = '物流信息'
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f'{self.express_company} {self.tracking_number}'
