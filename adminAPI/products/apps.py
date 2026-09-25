from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'

    def ready(self) -> None:
        """Register product signals."""
        import products.signals  # noqa: F401
