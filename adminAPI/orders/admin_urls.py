"""Admin order URL routes."""

from django.urls import path

from orders.admin_views import AdminCancelStatsView, AdminOrderCancelReviewView, AdminOrderCancelView

urlpatterns = [
    path('<int:pk>/cancel/', AdminOrderCancelView.as_view(), name='admin-order-cancel'),
    path('<int:pk>/cancel-review/', AdminOrderCancelReviewView.as_view(), name='admin-order-cancel-review'),
    path('cancel-stats/', AdminCancelStatsView.as_view(), name='admin-order-cancel-stats'),
]
