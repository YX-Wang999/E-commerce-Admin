"""Account views."""

import logging
import json

from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.captcha_trust import (
    TRUST_LOW,
    TRUST_MEDIUM,
    assess_login_trust,
    captcha_required_for_trust,
    get_device_id,
    record_ip_login_attempt,
    record_trusted_session,
)
from accounts.slider_captcha import (
    consume_verified_captcha,
    create_slider_captcha,
    verify_slider_captcha,
)
from accounts.login_guard import MAX_ATTEMPTS, clear_failures, is_locked, record_failure
from accounts.activation import (
    ActivationError,
    build_activation_link,
    create_activation_log,
    expire_pending_activation_logs,
    issue_password_reset,
    mark_activation_log_failed,
    save_user_activation_token,
    send_activation_email,
    send_password_reset_email,
    set_account_password,
)
from accounts.serializers import (
    ActivateAccountSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from audit.middleware import _get_client_ip
from audit.models import OperationLog
from accounts.models import ActivationLog
from accounts.scopes import filter_users_by_scope
from common.pagination import StandardPagination
from common.permissions import IsAdminRole
from common.response import error_response, success_response
from rbac.utils import get_user_menu_tree
from rbac.models import Menu, Role

logger = logging.getLogger(__name__)
User = get_user_model()

LOGIN_CODE_INVALID = 40002
LOGIN_CODE_DISABLED = 40003
LOGIN_CODE_LOCKED = 40004
LOGIN_CODE_CAPTCHA = 40005
LOGIN_CODE_USERNAME_NOT_FOUND = 40006
LOGIN_CODE_PASSWORD_WRONG = 40007
FORGOT_PASSWORD_MESSAGE = '如果该邮箱已注册，我们将发送密码重置邮件'


class CaptchaTrustView(APIView):
    """Assess captcha trust level for the current client session."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """Return high / medium / low trust for login captcha UX."""
        username = str(request.query_params.get('username', '')).strip()
        trust_level = assess_login_trust(request, username)
        return success_response(
            data={'trust_level': trust_level},
            message='信任等级已评估',
        )


class CaptchaView(APIView):
    """Return a fresh slider captcha puzzle."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """Generate slider captcha id and puzzle images."""
        data = create_slider_captcha()
        return success_response(data=data, message='验证码已生成')


class CaptchaVerifyView(APIView):
    """Verify slider drag trail and puzzle offset."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Validate slider captcha before login."""
        captcha_id = request.data.get('captcha_id')
        offset = request.data.get('offset')
        trail = request.data.get('trail')
        if isinstance(trail, str):
            try:
                trail = json.loads(trail)
            except json.JSONDecodeError:
                trail = None
        verified = verify_slider_captcha(captcha_id, offset, trail)
        if not verified:
            return error_response('滑块验证失败，请重试', code=40005)
        return success_response(data={'verified': True}, message='验证通过')


class LoginView(APIView):
    """Username/password login."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Authenticate user and return JWT tokens."""
        username = str(request.data.get('username', '')).strip()
        password = request.data.get('password', '')
        captcha_id = request.data.get('captcha_id')
        client_ip = _get_client_ip(request) or 'unknown'
        device_id = get_device_id(request)

        record_ip_login_attempt(client_ip)

        if not username:
            return error_response('请输入用户名', code=40001)
        if not password:
            return error_response('请输入密码', code=40001)

        if is_locked(username, client_ip):
            return error_response('登录失败次数过多，请稍后再试', code=LOGIN_CODE_LOCKED)

        trust_level = assess_login_trust(request, username)
        captcha_ok = bool(captcha_id and consume_verified_captcha(captcha_id))
        if captcha_required_for_trust(trust_level) and not captcha_ok:
            payload = {
                'require_captcha': True,
                'trust_level': trust_level,
                'captcha_mode': 'pre_action' if trust_level == TRUST_LOW else 'post_login',
            }
            message = '请先完成安全验证'
            if trust_level == TRUST_MEDIUM:
                payload.update(create_slider_captcha())
                message = '请完成安全验证后继续登录'
            return error_response(message, code=LOGIN_CODE_CAPTCHA, data=payload)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            count = record_failure(username, client_ip)
            remaining = max(0, MAX_ATTEMPTS - count)
            return error_response(
                '此用户名不存在',
                code=LOGIN_CODE_USERNAME_NOT_FOUND,
                data={'remaining_attempts': remaining},
            )

        if not user.is_active:
            count = record_failure(username, client_ip)
            remaining = max(0, MAX_ATTEMPTS - count)
            pending_activation = user.activation_logs.filter(status='pending').exists()
            if pending_activation or getattr(user, 'activation_token', None):
                message = '账号未激活，请查收邮件完成激活'
            else:
                message = '账号已被禁用'
            return error_response(
                message,
                code=LOGIN_CODE_DISABLED,
                data={'remaining_attempts': remaining},
            )

        if not user.check_password(password):
            count = record_failure(username, client_ip)
            remaining = max(0, MAX_ATTEMPTS - count)
            return error_response(
                '密码错误',
                code=LOGIN_CODE_PASSWORD_WRONG,
                data={'remaining_attempts': remaining},
            )

        clear_failures(username, client_ip)
        record_trusted_session(username, client_ip, device_id)
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data
        menus = get_user_menu_tree(user)
        response_code = 1001 if user.is_first_login else 0
        response_message = '首次登录，请修改密码' if user.is_first_login else '登录成功'
        return success_response(
            data={
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': user_data,
                'menus': menus,
            },
            message=response_message,
            code=response_code,
        )


class CustomTokenRefreshView(TokenRefreshView):
    """Token refresh with unified response format."""

    permission_classes = [AllowAny]

    def post(self, request: Request, *args, **kwargs) -> Response:
        """Refresh access token."""
        try:
            response = super().post(request, *args, **kwargs)
            if response.status_code != status.HTTP_200_OK:
                return error_response('Refresh Token 无效', code=40100, http_status=401)
            return success_response(
                data={'access': response.data['access']},
                message='Token 刷新成功',
            )
        except Exception:
            logger.exception('Token refresh failed')
            return error_response('Refresh Token 无效', code=40100, http_status=401)


class ProfileView(APIView):
    """Current user profile and menus."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return current user info and menus."""
        user = request.user
        return success_response(
            data={
                'user': UserSerializer(user).data,
                'menus': get_user_menu_tree(user),
            },
        )


class ChangePasswordView(APIView):
    """Current user change password."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Validate old password and update to new password."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            if isinstance(message, dict):
                message = next(iter(message.values()))[0]
            return error_response(str(message))
        try:
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.is_first_login = False
            user.save(update_fields=['password', 'is_first_login'])
        except Exception:
            logger.exception('Change password failed for user: %s', request.user.username)
            return error_response('密码修改失败', code=50000, http_status=500)
        return success_response(message='密码修改成功')


def _serializer_first_error(errors: dict) -> str:
    """Extract first validation error message."""
    value = next(iter(errors.values()))
    if isinstance(value, list):
        return str(value[0])
    if isinstance(value, dict):
        return _serializer_first_error(value)
    return str(value)


def _get_or_create_customer_role() -> Role:
    """Return mall customer role with dashboard menu only."""
    role, _ = Role.objects.get_or_create(
        code='customer',
        defaults={
            'name': '商城用户',
            'description': '商城注册用户，仅访问仪表盘',
            'is_active': True,
        },
    )
    if not role.menus.exists():
        dashboard = Menu.objects.filter(name='Dashboard').first()
        if dashboard:
            role.menus.set([dashboard])
    return role


class RegisterView(APIView):
    """Deprecated: mall registration moved to /api/customers/auth/register/."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        return error_response('请使用手机号注册：/api/customers/auth/register/')


class ForgotPasswordView(APIView):
    """Send password reset email for forgotten password."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        """Accept email and send reset link when account exists and is active."""
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        email = serializer.validated_data['email'].strip().lower()
        user = User.objects.filter(email__iexact=email).first()
        if user and user.is_active and user.email:
            try:
                reset_data = issue_password_reset(user)
                send_password_reset_email(user, reset_data)
            except Exception:
                logger.exception(
                    'Send password reset email failed: user=%s',
                    user.username,
                )
        return success_response(message=FORGOT_PASSWORD_MESSAGE)


class UserViewSet(viewsets.ModelViewSet):
    """User CRUD viewset."""

    queryset = User.objects.select_related('department').prefetch_related('roles').prefetch_related(
        Prefetch(
            'activation_logs',
            queryset=ActivationLog.objects.order_by('-sent_at'),
        ),
    ).all()
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter staff users by role data scope (exclude mall customers)."""
        queryset = super().get_queryset().exclude(roles__code='customer').distinct()
        return filter_users_by_scope(queryset, self.request.user)

    def get_serializer_class(self):
        """Return serializer by action."""
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ('update', 'partial_update'):
            return UserUpdateSerializer
        return UserSerializer

    def list(self, request: Request, *args, **kwargs) -> Response:
        """List users."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        """Retrieve a user."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create a user."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            user = serializer.save()
        except Exception:
            logger.exception('Create user failed')
            return error_response('创建用户失败', code=50000, http_status=500)
        return success_response(
            data=UserSerializer(user).data,
            message='创建成功',
            http_status=status.HTTP_201_CREATED,
        )

    def update(self, request: Request, *args, **kwargs) -> Response:
        """Update a user."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            user = serializer.save()
        except Exception:
            logger.exception('Update user failed')
            return error_response('更新用户失败', code=50000, http_status=500)
        return success_response(data=UserSerializer(user).data, message='更新成功')

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Delete a user."""
        instance = self.get_object()
        if instance.is_superuser:
            return error_response('不能删除超级管理员')
        try:
            instance.delete()
        except Exception:
            logger.exception('Delete user failed')
            return error_response('删除用户失败', code=50000, http_status=500)
        return success_response(message='删除成功')

    @action(
        detail=True,
        methods=['post'],
        url_path='reset_password',
        permission_classes=[IsAuthenticated, IsAdminRole],
    )
    def reset_password(self, request: Request, pk: int | None = None) -> Response:
        """Reset target user password by admin."""
        target_user = self.get_object()
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            target_user.set_password(serializer.validated_data['new_password'])
            target_user.is_first_login = True
            target_user.save(update_fields=['password', 'is_first_login'])
            OperationLog.objects.create(
                user=request.user,
                username=request.user.username,
                module='用户管理',
                action=OperationLog.ACTION_UPDATE,
                resource='用户密码',
                resource_id=str(target_user.id),
                detail=(
                    f'管理员 {request.user.username} 重置了用户 '
                    f'{target_user.username} 的密码'
                ),
                ip=_get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
                request_method=request.method,
                request_path=request.path[:512],
            )
        except Exception:
            logger.exception(
                'Reset password failed: operator=%s target=%s',
                request.user.username,
                target_user.username,
            )
            return error_response('重置密码失败', code=50000, http_status=500)
        return success_response(message='密码重置成功')

    @action(
        detail=True,
        methods=['post'],
        url_path='send_activation',
        permission_classes=[IsAuthenticated, IsAdminRole],
    )
    def send_activation(self, request: Request, pk: int | None = None) -> Response:
        """Generate activation link and send email to user."""
        target_user = self.get_object()
        if not target_user.email:
            return error_response('该用户未设置邮箱，无法发送')
        activation_log = None
        try:
            expire_pending_activation_logs(target_user)
            activation_data = build_activation_link(target_user.id)
            activation_log = create_activation_log(target_user, activation_data['token'])
            save_user_activation_token(target_user, activation_data['token'])
            send_activation_email(target_user, activation_data)
            OperationLog.objects.create(
                user=request.user,
                username=request.user.username,
                module='用户管理',
                action=OperationLog.ACTION_OTHER,
                resource='账号激活',
                resource_id=str(target_user.id),
                detail=(
                    f'管理员 {request.user.username} 向用户 '
                    f'{target_user.username}({target_user.email}) 发送激活邮件'
                ),
                ip=_get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
                request_method=request.method,
                request_path=request.path[:512],
            )
        except RuntimeError as exc:
            if activation_log is not None:
                try:
                    mark_activation_log_failed(activation_log)
                except Exception:
                    logger.exception('Mark activation log failed')
            logger.warning(
                'Send activation failed: operator=%s target=%s reason=%s',
                request.user.username,
                target_user.username,
                exc,
            )
            return error_response(str(exc), code=50000, http_status=500)
        except Exception:
            if activation_log is not None:
                try:
                    mark_activation_log_failed(activation_log)
                except Exception:
                    logger.exception('Mark activation log failed')
            logger.exception(
                'Send activation failed: operator=%s target=%s',
                request.user.username,
                target_user.username,
            )
            return error_response('发送激活邮件失败', code=50000, http_status=500)
        return success_response(
            data={
                'email': target_user.email,
                'uid': activation_data['uid'],
                'token': activation_data['token'],
                'activation_url': activation_data['activation_url'],
                'expires_in_hours': activation_data['expires_in_hours'],
            },
            message='激活邮件已发送',
        )

    @action(
        detail=False,
        methods=['post'],
        url_path='activate',
        permission_classes=[AllowAny],
    )
    def activate(self, request: Request) -> Response:
        """Activate account or reset password with uid and token."""
        serializer = ActivateAccountSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        mode = serializer.validated_data.get('mode', 'activation')
        try:
            user = set_account_password(
                uid=serializer.validated_data['uid'],
                token=serializer.validated_data['token'],
                password=serializer.validated_data['password'],
                mode=mode,
            )
        except ActivationError as exc:
            return error_response(exc.message)
        except Exception:
            logger.exception('Account password setup failed')
            if mode == 'reset_password':
                return error_response('密码重置失败', code=50000, http_status=500)
            return error_response('账号激活失败', code=50000, http_status=500)
        if mode == 'reset_password':
            return success_response(
                data={'username': user.username},
                message='密码重置成功，请前往登录',
            )
        return success_response(
            data={'username': user.username},
            message='账号激活成功，请前往登录',
        )
