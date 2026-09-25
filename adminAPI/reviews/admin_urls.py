"""Admin review URL routes."""

from django.urls import path

from reviews.admin_views import AdminReviewDeleteView, AdminReviewListView

urlpatterns = [
    path('', AdminReviewListView.as_view(), name='admin-review-list'),
    path('<int:pk>/', AdminReviewDeleteView.as_view(), name='admin-review-delete'),
]
