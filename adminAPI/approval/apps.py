from django.apps import AppConfig


class ApprovalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'approval'
    verbose_name = '统一审核'

    def ready(self) -> None:
        import approval.signals  # noqa: F401
