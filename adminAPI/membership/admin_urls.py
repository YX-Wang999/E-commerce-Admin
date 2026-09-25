"""Admin membership routes."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from membership.admin_views import AdminCustomerMembershipView, MemberLevelViewSet

router = DefaultRouter()
router.register('levels', MemberLevelViewSet, basename='admin-membership-level')

urlpatterns = [
    path('customers/<int:customer_id>/', AdminCustomerMembershipView.as_view(), name='admin-customer-membership'),
    *router.urls,
]
