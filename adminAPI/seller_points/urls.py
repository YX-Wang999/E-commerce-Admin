"""Customer seller points URL routes."""

from django.urls import path

from seller_points.customer_views import CustomerSellerPointsCheckoutView

urlpatterns = [
    path('checkout/', CustomerSellerPointsCheckoutView.as_view(), name='customer-seller-points-checkout'),
]
