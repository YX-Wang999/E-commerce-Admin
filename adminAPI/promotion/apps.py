"""Promotion app configuration."""

from django.apps import AppConfig


class PromotionConfig(AppConfig):
    """Promotion application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'promotion'
    verbose_name = '促销管理'
