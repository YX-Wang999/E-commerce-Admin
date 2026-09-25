"""Logistics URL routes."""

from django.urls import path

from logistics.views import ExpressCompaniesView, LogisticsTrackView, LogisticsWebhookView

urlpatterns = [
    path('express-companies/', ExpressCompaniesView.as_view(), name='logistics-express-companies'),
    path('<int:order_id>/track/', LogisticsTrackView.as_view(), name='logistics-track'),
    path('webhook/', LogisticsWebhookView.as_view(), name='logistics-webhook'),
]
