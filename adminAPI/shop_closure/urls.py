"""Shop closure URL routes."""

from django.urls import path

from shop_closure.admin_views import (
    AdminClosureApproveView,
    AdminClosureCompleteView,
    AdminClosureDetailView,
    AdminClosureExportView,
    AdminClosureListView,
    AdminClosureRejectView,
)
from shop_closure.seller_views import SellerClosureApplicationView, SellerClosureConditionsView

urlpatterns = [
    path('seller/closure/conditions/', SellerClosureConditionsView.as_view(), name='seller-closure-conditions'),
    path('seller/closure/application/', SellerClosureApplicationView.as_view(), name='seller-closure-application'),
    path('admin/closures/', AdminClosureListView.as_view(), name='admin-closure-list'),
    path('admin/closures/export/', AdminClosureExportView.as_view(), name='admin-closure-export'),
    path('admin/closures/<int:pk>/', AdminClosureDetailView.as_view(), name='admin-closure-detail'),
    path('admin/closures/<int:pk>/approve/', AdminClosureApproveView.as_view(), name='admin-closure-approve'),
    path('admin/closures/<int:pk>/reject/', AdminClosureRejectView.as_view(), name='admin-closure-reject'),
    path('admin/closures/<int:pk>/complete/', AdminClosureCompleteView.as_view(), name='admin-closure-complete'),
]
