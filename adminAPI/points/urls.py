"""Points URL routes."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from points.views import (
    PointsAccountViewSet,
    PointsAdjustView,
    PointsCheckoutView,
    PointsMallTransactionsView,
    PointsProfileView,
    PointsPublicRulesView,
    PointsRuleViewSet,
    PointsSignInView,
    PointsTransactionViewSet,
)

router = DefaultRouter()
router.register('accounts', PointsAccountViewSet, basename='points-account')
router.register('transactions', PointsTransactionViewSet, basename='points-transaction')
router.register('rules', PointsRuleViewSet, basename='points-rule')

urlpatterns = [
    path('profile/', PointsProfileView.as_view(), name='points-profile'),
    path('checkout/', PointsCheckoutView.as_view(), name='points-checkout'),
    path('sign-in/', PointsSignInView.as_view(), name='points-sign-in'),
    path('mall/transactions/', PointsMallTransactionsView.as_view(), name='points-mall-transactions'),
    path('rules/public/', PointsPublicRulesView.as_view(), name='points-rules-public'),
    path('adjust/', PointsAdjustView.as_view(), name='points-adjust'),
    path('', include(router.urls)),
]
