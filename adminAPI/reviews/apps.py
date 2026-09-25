"""Product reviews application."""

from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reviews'
    verbose_name = '商品评价'

    def ready(self) -> None:
        """Register signal handlers."""
        import reviews.signals  # noqa: F401
