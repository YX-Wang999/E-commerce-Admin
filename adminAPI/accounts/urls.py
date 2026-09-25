"""Account URL routes."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts.views import (
    CaptchaTrustView,
    CaptchaVerifyView,
    CaptchaView,
    ChangePasswordView,
    CustomTokenRefreshView,
    ForgotPasswordView,
    LoginView,
    ProfileView,
    RegisterView,
    UserViewSet,
)
from accounts.department_views import DepartmentViewSet
from accounts.org_views import OrgChartView

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('departments', DepartmentViewSet, basename='department')

urlpatterns = [
    path('auth/captcha/trust/', CaptchaTrustView.as_view(), name='auth-captcha-trust'),
    path('auth/captcha/verify/', CaptchaVerifyView.as_view(), name='auth-captcha-verify'),
    path('auth/captcha/', CaptchaView.as_view(), name='auth-captcha'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/refresh/', CustomTokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/profile/', ProfileView.as_view(), name='auth-profile'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='auth-change-password'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='auth-forgot-password'),
    path('org/chart/', OrgChartView.as_view(), name='org-chart'),
    path('', include(router.urls)),
]
