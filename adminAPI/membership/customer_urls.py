"""Customer membership routes."""

from django.urls import path

from membership.customer_views import (
    MembershipCheckinView,
    MembershipGrowthLogsView,
    MembershipLevelUpView,
    MembershipLevelsView,
    MembershipMyProfileView,
)

urlpatterns = [
    path('levels/', MembershipLevelsView.as_view(), name='membership-levels'),
    path('my-profile/', MembershipMyProfileView.as_view(), name='membership-my-profile'),
    path('growth-logs/', MembershipGrowthLogsView.as_view(), name='membership-growth-logs'),
    path('checkin/', MembershipCheckinView.as_view(), name='membership-checkin'),
    path('level-up/', MembershipLevelUpView.as_view(), name='membership-level-up'),
]
