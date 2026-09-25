"""Customer URL routes."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from customers.auth_views import (
    CustomerLoginView,
    CustomerProfileView,
    CustomerRefreshView,
    CustomerRegisterView,
    CustomerResetPasswordView,
    SendSmsView,
)
from customers.views import CustomerViewSet
from notification.views import (
    CustomerNotificationListView,
    CustomerNotificationReadAllView,
    CustomerNotificationReadView,
    CustomerNotificationUnreadCountView,
)

router = DefaultRouter()
router.register('', CustomerViewSet, basename='customer')

urlpatterns = [
    path('auth/send-sms/', SendSmsView.as_view(), name='customer-send-sms'),
    path('auth/register/', CustomerRegisterView.as_view(), name='customer-register'),
    path('auth/login/', CustomerLoginView.as_view(), name='customer-login'),
    path('auth/refresh/', CustomerRefreshView.as_view(), name='customer-refresh'),
    path('auth/reset-password/', CustomerResetPasswordView.as_view(), name='customer-reset-password'),
    path('auth/profile/', CustomerProfileView.as_view(), name='customer-profile'),
    # Must be registered before router {pk} routes — otherwise
    # /customers/notifications/ is captured as customer pk="notifications".
    path('notifications/', CustomerNotificationListView.as_view(), name='customer-notifications'),
    path('notifications/unread-count/', CustomerNotificationUnreadCountView.as_view(), name='customer-notifications-unread'),
    path('notifications/read-all/', CustomerNotificationReadAllView.as_view(), name='customer-notifications-read-all'),
    path('notifications/<int:pk>/read/', CustomerNotificationReadView.as_view(), name='customer-notification-read'),
    path('', include(router.urls)),
]
