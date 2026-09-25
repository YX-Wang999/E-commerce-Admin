"""Chat URL routes."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from chat.complaint_views import ComplaintViewSet
from chat.views import ConversationViewSet

router = DefaultRouter()
router.register('conversations', ConversationViewSet, basename='chat-conversation')
router.register('complaints', ComplaintViewSet, basename='chat-complaint')

urlpatterns = [
    path('', include(router.urls)),
]
