"""Group buy mall URLs."""

from django.urls import path

from promotion.mall_views import GroupBuyActivitiesView, GroupBuyJoinView

urlpatterns = [
    path('activities/', GroupBuyActivitiesView.as_view(), name='groupbuy-activities'),
    path('<int:pk>/join/', GroupBuyJoinView.as_view(), name='groupbuy-join'),
]
