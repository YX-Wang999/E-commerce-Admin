"""WebSocket URL routing for chat."""

from django.urls import re_path

from chat.consumers import ChatConsumer
from notification.consumers import NotifyConsumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<conversation_id>\d+)/$', ChatConsumer.as_asgi()),
    re_path(r'ws/notify/$', NotifyConsumer.as_asgi()),
]
