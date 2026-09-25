"""User account activation link utilities."""

import logging
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from accounts.email_utils import send_system_email
from accounts.models import ActivationLog, User

logger = logging.getLogger(__name__)

ACTIVATION_SALT = 'account-activation'
ACTIVATION_MAX_AGE = 60 * 60 * 24


class ActivationError(Exception):
    """Raised when activation validation fails."""

    def __init__(self, message: str) -> None:
        """Initialize activation error."""
        self.message = message
        super().__init__(message)


def encode_uid(user_id: int) -> str:
    """Encode user id to url-safe base64 string."""
    return urlsafe_base64_encode(force_bytes(user_id))


def decode_uid(uid: str) -> int:
    """Decode url-safe base64 uid to user id."""
    return int(force_str(urlsafe_base64_decode(uid)))


def generate_activation_token(user_id: int) -> str:
    """Generate signed activation token valid for 24 hours."""
    signer = TimestampSigner(salt=ACTIVATION_SALT)
    return signer.sign(str(user_id))


def verify_activation_token(token: str, max_age: int = ACTIVATION_MAX_AGE) -> int:
    """Verify activation token and return user id."""
    signer = TimestampSigner(salt=ACTIVATION_SALT)
    user_id = signer.unsign(token, max_age=max_age)
    return int(user_id)


def build_activation_link(user_id: int) -> dict[str, Any]:
    """Build activation link with uid and token."""
    uid = encode_uid(user_id)
    token = generate_activation_token(user_id)
    base_url = getattr(
        settings,
        'ACTIVATION_LINK_BASE',
        'http://localhost:5173',
    ).rstrip('/')
    activation_url = f'{base_url}/activate?uid={uid}&token={token}'
    return {
        'uid': uid,
        'token': token,
        'activation_url': activation_url,
        'expires_in_hours': ACTIVATION_MAX_AGE // 3600,
    }


def expire_pending_activation_logs(user: User) -> None:
    """Mark pending activation logs as expired before resending."""
    ActivationLog.objects.filter(
        user=user,
        status=ActivationLog.STATUS_PENDING,
    ).update(status=ActivationLog.STATUS_EXPIRED)


def create_activation_log(user: User, token: str) -> ActivationLog:
    """Create a pending activation log record."""
    now = timezone.now()
    return ActivationLog.objects.create(
        user=user,
        token=token,
        status=ActivationLog.STATUS_PENDING,
        expired_at=now + timedelta(seconds=ACTIVATION_MAX_AGE),
    )


def mark_activation_log_failed(activation_log: ActivationLog) -> None:
    """Mark activation log as failed."""
    activation_log.status = ActivationLog.STATUS_FAILED
    activation_log.save(update_fields=['status'])


def mark_activation_log_activated(user: User, token: str) -> None:
    """Mark activation log as activated."""
    ActivationLog.objects.filter(
        user=user,
        token=token,
        status=ActivationLog.STATUS_PENDING,
    ).update(
        status=ActivationLog.STATUS_ACTIVATED,
        activated_at=timezone.now(),
    )


def get_activation_display_status(log: ActivationLog | None) -> tuple[str, str]:
    """Return activation status code and display label."""
    if log is None:
        return 'none', '未发送'
    if log.status == ActivationLog.STATUS_PENDING and log.expired_at <= timezone.now():
        return ActivationLog.STATUS_EXPIRED, '已过期（可重发）'
    status_labels = {
        ActivationLog.STATUS_PENDING: '待激活',
        ActivationLog.STATUS_ACTIVATED: '已激活',
        ActivationLog.STATUS_EXPIRED: '已过期（可重发）',
        ActivationLog.STATUS_FAILED: '发送失败（可重发）',
    }
    return log.status, status_labels.get(log.status, '未发送')


def save_user_activation_token(user: User, token: str) -> None:
    """Persist activation token and disable account until activated."""
    user.activation_token = token
    user.token_created_at = timezone.now()
    user.is_active = False
    user.save(update_fields=['activation_token', 'token_created_at', 'is_active'])


def build_password_reset_link(user_id: int) -> dict[str, Any]:
    """Build password reset link with uid and token."""
    uid = encode_uid(user_id)
    token = generate_activation_token(user_id)
    base_url = getattr(
        settings,
        'ACTIVATION_LINK_BASE',
        'http://localhost:5173',
    ).rstrip('/')
    reset_url = f'{base_url}/reset-password?uid={uid}&token={token}'
    return {
        'uid': uid,
        'token': token,
        'reset_url': reset_url,
        'expires_in_hours': ACTIVATION_MAX_AGE // 3600,
    }


def save_user_password_reset_token(user: User, token: str) -> None:
    """Persist password reset token without changing account active status."""
    user.activation_token = token
    user.token_created_at = timezone.now()
    user.save(update_fields=['activation_token', 'token_created_at'])


def _validate_account_token(uid: str, token: str, *, mode: str = 'activation') -> User:
    """Validate uid/token pair and return the matching user."""
    try:
        user_id = decode_uid(uid)
    except (ValueError, TypeError):
        raise ActivationError('链接无效') from None

    try:
        signed_user_id = verify_activation_token(token)
    except SignatureExpired:
        if mode == 'reset_password':
            raise ActivationError(
                '链接已过期，请重新发送密码重置邮件',
            ) from None
        raise ActivationError(
            '激活链接已过期（超过 24 小时），请联系管理员重新发送',
        ) from None
    except BadSignature:
        raise ActivationError('链接无效') from None

    if signed_user_id != user_id:
        raise ActivationError('链接无效')

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise ActivationError('链接无效') from None

    if not user.activation_token:
        if mode == 'reset_password':
            raise ActivationError('该链接已失效，请重新发送密码重置邮件')
        if user.is_active:
            raise ActivationError('该链接已被使用，无需重复激活，请直接登录')
        raise ActivationError('激活链接无效，请联系管理员重新发送')

    if user.activation_token != token:
        raise ActivationError('链接无效')

    if not user.token_created_at:
        raise ActivationError('链接无效')

    if timezone.now() - user.token_created_at > timedelta(seconds=ACTIVATION_MAX_AGE):
        if mode == 'reset_password':
            raise ActivationError('链接已过期，请重新发送密码重置邮件')
        raise ActivationError(
            '激活链接已过期（超过 24 小时），请联系管理员重新发送',
        )

    return user


def set_account_password(
    uid: str,
    token: str,
    password: str,
    *,
    mode: str = 'activation',
) -> User:
    """Validate token and set password for activation or password reset."""
    user = _validate_account_token(uid, token, mode=mode)
    user.set_password(password)
    user.activation_token = ''
    user.token_created_at = None

    if mode == 'reset_password':
        user.save(update_fields=['password', 'activation_token', 'token_created_at'])
    else:
        user.is_active = True
        user.is_first_login = False
        user.save(update_fields=[
            'password',
            'is_active',
            'is_first_login',
            'activation_token',
            'token_created_at',
        ])

    mark_activation_log_activated(user, token)
    return user


def activate_user_account(uid: str, token: str, password: str) -> User:
    """Validate activation credentials and activate user account."""
    return set_account_password(uid, token, password, mode='activation')


def issue_password_reset(user: User) -> dict[str, Any]:
    """Generate reset token, persist it, and return link payload."""
    expire_pending_activation_logs(user)
    reset_data = build_password_reset_link(user.id)
    create_activation_log(user, reset_data['token'])
    save_user_password_reset_token(user, reset_data['token'])
    return reset_data


def send_activation_email(user: User, activation_data: dict[str, Any]) -> None:
    """Send activation link to user email."""
    display_name = user.nickname or user.username
    expires_in_hours = activation_data['expires_in_hours']
    activation_url = activation_data['activation_url']
    subject = '账号激活通知'
    message = (
        f'您好 {display_name}，\n\n'
        f'管理员已为您创建后台账号，请点击以下链接激活（{expires_in_hours} 小时内有效）：\n\n'
        f'{activation_url}\n\n'
        f'如非本人操作，请忽略此邮件。'
    )
    send_system_email(
        subject=subject,
        message=message,
        recipient_list=[user.email],
        fail_silently=False,
    )
    logger.info('[Activation Email] sent to %s', user.email)


def send_password_reset_email(user: User, reset_data: dict[str, Any]) -> None:
    """Send password reset link to user email."""
    reset_url = reset_data['reset_url']
    subject = f'【管理系统】密码重置通知 - {user.username}'
    html_message = f'''
    <div style="font-family: 'Microsoft YaHei', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e8e8e8; border-radius: 8px;">
        <h2 style="color: #1890ff;">🔐 密码重置请求</h2>
        <p>您好 <strong>{user.username}</strong>，</p>
        <p>我们收到了您的密码重置请求。请点击下方按钮设置新密码：</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}"
               style="background-color: #1890ff; color: #fff; padding: 12px 40px; border-radius: 4px; text-decoration: none; font-size: 16px;">
               重置密码
            </a>
        </div>
        <p style="color: #ff4d4f; font-size: 14px;">⏰ 该链接将在 <strong>24 小时</strong> 后失效。</p>
        <p style="color: #999; font-size: 12px;">如果这不是您本人操作，请忽略此邮件，您的密码将不会被修改。</p>
        <hr style="border: none; border-top: 1px solid #f0f0f0;" />
        <p style="color: #999; font-size: 12px;">此邮件由系统自动发送，请勿直接回复。</p>
    </div>
    '''
    send_system_email(
        subject=subject,
        message='请使用支持 HTML 的邮件客户端查看此邮件。',
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
    logger.info('[Password Reset Email] sent to %s', user.email)


def log_activation_link(username: str, activation_data: dict[str, Any]) -> None:
    """Log activation link for debugging."""
    logger.info(
        '[Activation Email] recipient=%s url=%s expires_in=%sh',
        username,
        activation_data['activation_url'],
        activation_data['expires_in_hours'],
    )
