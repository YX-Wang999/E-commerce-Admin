from django.apps import AppConfig


class ShopRatingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop_rating'
    verbose_name = '店铺评分'

    def ready(self) -> None:
        import shop_rating.signals  # noqa: F401
