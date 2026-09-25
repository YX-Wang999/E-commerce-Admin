"""Notification URL routes."""

from django.urls import path

from notification.views import (
    CustomerNotificationListView,
    CustomerNotificationReadAllView,
    CustomerNotificationReadView,
    CustomerNotificationUnreadCountView,
    SellerNotificationListView,
    SellerNotificationReadAllView,
    SellerNotificationReadView,
    SellerNotificationUnreadCountView,
    StaffNotificationListView,
    StaffNotificationReadAllView,
    StaffNotificationReadView,
    StaffNotificationUnreadCountView,
)

urlpatterns = [
    path('notifications/', StaffNotificationListView.as_view(), name='staff-notifications'),
    path('notifications/unread-count/', StaffNotificationUnreadCountView.as_view(), name='staff-notifications-unread'),
    path('notifications/read-all/', StaffNotificationReadAllView.as_view(), name='staff-notifications-read-all'),
    path('notifications/<int:pk>/read/', StaffNotificationReadView.as_view(), name='staff-notification-read'),
    path('seller/notifications/', SellerNotificationListView.as_view(), name='seller-notifications'),
    path('seller/notifications/unread-count/', SellerNotificationUnreadCountView.as_view(), name='seller-notifications-unread'),
    path('seller/notifications/read-all/', SellerNotificationReadAllView.as_view(), name='seller-notifications-read-all'),
    path('seller/notifications/<int:pk>/read/', SellerNotificationReadView.as_view(), name='seller-notification-read'),
    path('customer/notifications/', CustomerNotificationListView.as_view(), name='customer-notifications'),
    path('customer/notifications/unread-count/', CustomerNotificationUnreadCountView.as_view(), name='customer-notifications-unread'),
    path('customer/notifications/read-all/', CustomerNotificationReadAllView.as_view(), name='customer-notifications-read-all'),
    path('customer/notifications/<int:pk>/read/', CustomerNotificationReadView.as_view(), name='customer-notification-read'),
]
