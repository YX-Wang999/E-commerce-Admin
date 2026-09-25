"""Customer feedback URL routes."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from feedback.views import CustomerFeedbackMineView, CustomerFeedbackViewSet, FeedbackSubmitView

router = DefaultRouter()
router.register('', CustomerFeedbackViewSet, basename='feedback')

urlpatterns = [
    path('mine/', CustomerFeedbackMineView.as_view(), name='feedback-mine'),
    path('submit/', FeedbackSubmitView.as_view(), name='feedback-submit'),
    path('', include(router.urls)),
]
