"""Order URL routes."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from orders.views import CustomerOrderSummaryView, OrderPendingSummaryView, OrderViewSet, RefundViewSet

router = DefaultRouter()
router.register('refunds', RefundViewSet, basename='refund')
router.register('', OrderViewSet, basename='order')

urlpatterns = [
    path('mine-summary/', CustomerOrderSummaryView.as_view(), name='order-mine-summary'),
    path('pending-summary/', OrderPendingSummaryView.as_view(), name='order-pending-summary'),
    path('', include(router.urls)),
]
