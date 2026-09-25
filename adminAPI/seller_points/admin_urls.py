"""Admin seller points URL routes."""

from django.urls import path

from seller_points.admin_views import AdminSellerPointsOverviewView, AdminSellerPointsTransactionListView

urlpatterns = [
    path('overview/', AdminSellerPointsOverviewView.as_view(), name='admin-seller-points-overview'),
    path('transactions/', AdminSellerPointsTransactionListView.as_view(), name='admin-seller-points-transactions'),
]
