"""System email helpers (SMTP / QQ Mail)."""

from __future__ import annotations

import logging
import smtplib
import socket
from typing import Sequence

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

_PLACEHOLDER_MARKERS = (
    '你的',
    'your_',
    'example.com',
    'change-me',
    'your_password',
    'your_email',
)


def _looks_like_placeholder(value: str) -> bool:
    normalized = (value or '').strip().lower()
    if not normalized:
        return True
    return any(marker in normalized for marker in _PLACEHOLDER_MARKERS)


def is_email_configured() -> bool:
    """Return True when SMTP host and credentials are configured."""
    host = (settings.EMAIL_HOST or '').strip()
    user = (settings.EMAIL_HOST_USER or '').strip()
    password = (settings.EMAIL_HOST_PASSWORD or '').strip()
    if not host or not user or not password:
        return False
    if _looks_like_placeholder(user) or _looks_like_placeholder(password):
        return False
    return True


def get_email_config_hint() -> str:
    """Return setup hint when email is not ready."""
    if not (settings.EMAIL_HOST or '').strip():
        return (
            '邮件服务未配置：请在 adminAPI 目录创建 .env 文件'
            '（可复制 .env.example），填入 QQ 邮箱 SMTP 与 16 位授权码后重启后端'
        )
    if _looks_like_placeholder(settings.EMAIL_HOST_USER or ''):
        return '邮件服务未配置：请在 adminAPI/.env 中将 EMAIL_HOST_USER 改为真实 QQ 邮箱'
    if _looks_like_placeholder(settings.EMAIL_HOST_PASSWORD or ''):
        return (
            '邮件服务未配置：请在 adminAPI/.env 中将 EMAIL_HOST_PASSWORD '
            '改为 QQ 邮箱 16 位授权码（不是 QQ 登录密码）'
        )
    return '邮件服务未配置，请检查 adminAPI/.env 中的 SMTP 设置'


def get_from_email() -> str:
    """Return the fixed sender address for all outbound mail."""
    return settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER


def _translate_smtp_error(exc: Exception) -> str:
    message = str(exc).strip()
    lowered = message.lower()
    if isinstance(exc, smtplib.SMTPAuthenticationError) or '535' in message:
        return (
            'SMTP 登录失败：请确认 adminAPI/.env 中 '
            'EMAIL_HOST_PASSWORD 为 QQ 邮箱 16 位授权码（不是 QQ 登录密码）'
        )
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return (
            '连接 SMTP 服务器超时：请检查网络，或尝试改用 '
            'EMAIL_PORT=465、EMAIL_USE_SSL=True、EMAIL_USE_TLS=False'
        )
    if isinstance(exc, smtplib.SMTPConnectError) or 'connect' in lowered:
        return (
            '无法连接 SMTP 服务器：请确认 EMAIL_HOST=smtp.qq.com，'
            '端口与 TLS/SSL 设置正确'
        )
    if message:
        return f'邮件发送失败：{message}'
    return '邮件发送失败，请查看后端日志'


def send_system_email(
    *,
    subject: str,
    message: str,
    recipient_list: Sequence[str],
    html_message: str | None = None,
    fail_silently: bool = False,
) -> int:
    """
    Send email via configured SMTP.

    The sender is always DEFAULT_FROM_EMAIL so messages can reach any recipient.
    """
    recipients = [email.strip() for email in recipient_list if email and email.strip()]
    if not recipients:
        raise ValueError('收件人邮箱不能为空')

    if not is_email_configured():
        error_message = get_email_config_hint()
        logger.error('[Email] %s', error_message)
        if fail_silently:
            return 0
        raise RuntimeError(error_message)

    from_email = get_from_email()
    try:
        sent_count = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipients,
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as exc:
        error_message = _translate_smtp_error(exc)
        logger.exception('[Email] send failed from=%s to=%s', from_email, recipients)
        if fail_silently:
            return 0
        raise RuntimeError(error_message) from exc

    logger.info(
        '[Email] sent subject=%r from=%s to=%s count=%s',
        subject,
        from_email,
        recipients,
        sent_count,
    )
    return sent_count
