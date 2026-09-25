"""Points mall admin URL routes."""

from django.urls import path

from points_mall.admin_views import (
    AdminPointsMallItemDetailView,
    AdminPointsMallItemListView,
    AdminPointsMallOrderDetailView,
    AdminPointsMallOrderListView,
    AdminPointsMallOrderShipView,
    AdminPointsMallStatsView,
)

urlpatterns = [
    path('items/', AdminPointsMallItemListView.as_view(), name='admin-points-mall-items'),
    path('items/<int:pk>/', AdminPointsMallItemDetailView.as_view(), name='admin-points-mall-item-detail'),
    path('orders/', AdminPointsMallOrderListView.as_view(), name='admin-points-mall-orders'),
    path('orders/<int:pk>/', AdminPointsMallOrderDetailView.as_view(), name='admin-points-mall-order-detail'),
    path('orders/<int:pk>/ship/', AdminPointsMallOrderShipView.as_view(), name='admin-points-mall-order-ship'),
    path('stats/', AdminPointsMallStatsView.as_view(), name='admin-points-mall-stats'),
]
