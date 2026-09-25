from django.apps import AppConfig


class SellerPointsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'seller_points'
    verbose_name = '商家积分'

    def ready(self) -> None:
        import seller_points.signals  # noqa: F401
