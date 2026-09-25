"""Points mall URL routes."""

from django.urls import path

from points_mall.views import (
    PointsMallExchangeView,
    PointsMallItemDetailView,
    PointsMallItemListView,
    PointsMallOrderDetailView,
    PointsMallOrderListView,
)

urlpatterns = [
    path('items/', PointsMallItemListView.as_view(), name='points-mall-items'),
    path('items/<int:pk>/', PointsMallItemDetailView.as_view(), name='points-mall-item-detail'),
    path('items/<int:pk>/exchange/', PointsMallExchangeView.as_view(), name='points-mall-exchange'),
    path('orders/', PointsMallOrderListView.as_view(), name='points-mall-orders'),
    path('orders/<int:pk>/', PointsMallOrderDetailView.as_view(), name='points-mall-order-detail'),
]
