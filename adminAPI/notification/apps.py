from django.apps import AppConfig


class NotificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notification'
    verbose_name = '通知中心'

    def ready(self) -> None:
        import notification.signals  # noqa: F401
