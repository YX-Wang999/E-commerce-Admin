"""Aliyun SMS verification service."""

from __future__ import annotations

import json
import logging
import random
import string
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from customers.models import SmsVerificationCode

logger = logging.getLogger(__name__)

SMS_CODE_LENGTH = 6
SMS_CODE_TTL_MINUTES = 5


@dataclass
class AliyunSmsSendResult:
    code: str | None
    out_id: str | None


def _sms_resend_seconds() -> int:
    return getattr(settings, 'SMS_RESEND_SECONDS', 60)


def _generate_code() -> str:
    return ''.join(random.choices(string.digits, k=SMS_CODE_LENGTH))


def _can_send(phone: str, scene: str) -> bool:
    latest = (
        SmsVerificationCode.objects.filter(phone=phone, scene=scene, is_used=False)
        .order_by('-created_at')
        .first()
    )
    if latest is None:
        return True
    return (timezone.now() - latest.created_at).total_seconds() >= _sms_resend_seconds()


def _format_phone_for_aliyun(phone: str) -> str:
    """Aliyun Dypnsapi: China uses 11-digit national; others use digits without '+'."""
    digits = phone.lstrip('+').replace(' ', '')
    if digits.startswith('86') and len(digits) == 13:
        return digits[2:]
    return digits


def _create_dypns_client():
    from alibabacloud_dypnsapi20170525.client import Client as DypnsClient
    from alibabacloud_tea_openapi import models as open_api_models

    config = open_api_models.Config()
    config.endpoint = 'dypnsapi.aliyuncs.com'

    access_key_id = getattr(settings, 'ALIBABA_CLOUD_ACCESS_KEY_ID', '')
    access_key_secret = getattr(settings, 'ALIBABA_CLOUD_ACCESS_KEY_SECRET', '')
    if access_key_id and access_key_secret:
        config.access_key_id = access_key_id
        config.access_key_secret = access_key_secret
    else:
        try:
            from alibabacloud_credentials.client import Client as CredentialClient
        except ImportError as exc:
            raise ValueError('短信服务未配置，请联系管理员') from exc
        config.credential = CredentialClient()

    return DypnsClient(config)


def _is_aliyun_success(body) -> bool:
    if body is None:
        return False
    code = getattr(body, 'code', None)
    success = getattr(body, 'success', None)
    return str(code) == 'OK' or success is True


def _resolve_sms_template(scene: str) -> tuple[str, str]:
    """Pick sign name and template code by SMS scene.

    Register uses API/API-Python defaults; reset_password uses ChangepwdAPITemp-Python.
    """
    from customers.models import SmsVerificationCode

    if scene == SmsVerificationCode.SCENE_RESET_PASSWORD:
        sign_name = getattr(settings, 'ALIYUN_SMS_RESET_SIGN_NAME', settings.ALIYUN_SMS_SIGN_NAME)
        template_code = getattr(settings, 'ALIYUN_SMS_RESET_TEMPLATE_CODE', settings.ALIYUN_SMS_TEMPLATE_CODE)
    else:
        sign_name = settings.ALIYUN_SMS_SIGN_NAME
        template_code = settings.ALIYUN_SMS_TEMPLATE_CODE
    return sign_name, template_code


def _send_via_aliyun(phone: str, scene: str) -> AliyunSmsSendResult:
    """Send SMS via Aliyun Dypnsapi SendSmsVerifyCode."""
    try:
        from alibabacloud_dypnsapi20170525 import models as dypns_models
        from alibabacloud_tea_util import models as util_models
    except ImportError as exc:
        logger.exception('Aliyun SMS SDK not installed')
        raise ValueError(
            '短信 SDK 未安装，请在后端目录执行：pip install -r requirements.txt'
        ) from exc

    sign_name, template_code = _resolve_sms_template(scene)
    client = _create_dypns_client()
    request = dypns_models.SendSmsVerifyCodeRequest(
        sign_name=sign_name,
        template_code=template_code,
        phone_number=phone,
        template_param=json.dumps(
            {'code': '##code##', 'min': str(SMS_CODE_TTL_MINUTES)},
            ensure_ascii=False,
        ),
        return_verify_code=True,
        code_length=SMS_CODE_LENGTH,
        valid_time=SMS_CODE_TTL_MINUTES * 60,
    )
    runtime = util_models.RuntimeOptions()
    try:
        response = client.send_sms_verify_code_with_options(request, runtime)
    except Exception as exc:
        logger.exception('Aliyun SendSmsVerifyCode failed: phone=%s', phone)
        detail = getattr(exc, 'message', None) or str(exc)
        raise ValueError(f'短信发送失败：{detail}') from exc

    body = getattr(response, 'body', None)
    if not _is_aliyun_success(body):
        message = getattr(body, 'message', None) if body else None
        code = getattr(body, 'code', None) if body else None
        raise ValueError(f'短信发送失败：{message or code or "未知错误"}')

    model = getattr(body, 'model', None) if body else None
    verify_code = getattr(model, 'verify_code', None) if model else None
    out_id = getattr(model, 'out_id', None) if model else None
    logger.info('Aliyun SMS sent: phone=%s scene=%s template=%s has_code=%s', phone, scene, template_code, bool(verify_code))
    return AliyunSmsSendResult(
        code=str(verify_code) if verify_code else None,
        out_id=str(out_id) if out_id else None,
    )


def _check_via_aliyun(phone: str, verify_code: str, out_id: str | None = None) -> bool:
    """Verify SMS code via Aliyun CheckSmsVerifyCode."""
    try:
        from alibabacloud_dypnsapi20170525 import models as dypns_models
        from alibabacloud_tea_util import models as util_models
    except ImportError:
        return False

    client = _create_dypns_client()
    request = dypns_models.CheckSmsVerifyCodeRequest(
        phone_number=_format_phone_for_aliyun(phone),
        verify_code=verify_code.strip(),
        out_id=out_id or None,
        case_auth_policy=1,
    )
    runtime = util_models.RuntimeOptions()
    try:
        response = client.check_sms_verify_code_with_options(request, runtime)
    except Exception:
        logger.exception('Aliyun CheckSmsVerifyCode failed: phone=%s', phone)
        return False

    body = getattr(response, 'body', None)
    if not _is_aliyun_success(body):
        return False
    model = getattr(body, 'model', None) if body else None
    return getattr(model, 'verify_result', None) == 'PASS'


def send_verification_code(phone: str, scene: str) -> tuple[str, str | None]:
    """Create and send SMS code. Returns (user message, dev_code if applicable)."""
    if not _can_send(phone, scene):
        raise ValueError('发送过于频繁，请稍后再试')

    enabled = getattr(settings, 'ALIYUN_SMS_ENABLED', False)
    out_id = ''
    if enabled:
        result = _send_via_aliyun(_format_phone_for_aliyun(phone), scene)
        code = result.code or ''
        out_id = result.out_id or ''
        user_message = '验证码已发送'
        dev_code = None
    else:
        code = _generate_code()
        logger.info('[SMS][dev] phone=%s scene=%s code=%s', phone, scene, code)
        user_message = '验证码已发送（开发模式）'
        dev_code = code

    expires_at = timezone.now() + timedelta(minutes=SMS_CODE_TTL_MINUTES)
    SmsVerificationCode.objects.create(
        phone=phone,
        code=code,
        scene=scene,
        out_id=out_id,
        expires_at=expires_at,
    )
    return user_message, dev_code


def verify_code(phone: str, scene: str, code: str) -> bool:
    """Validate SMS code and mark as used."""
    normalized = (code or '').strip()
    if not normalized:
        return False

    record = (
        SmsVerificationCode.objects.filter(
            phone=phone,
            scene=scene,
            is_used=False,
        )
        .order_by('-created_at')
        .first()
    )
    if record is None:
        return False
    if record.expires_at < timezone.now():
        return False

    enabled = getattr(settings, 'ALIYUN_SMS_ENABLED', False)
    verified = False
    if record.code and record.code == normalized:
        verified = True
    elif enabled:
        verified = _check_via_aliyun(phone, normalized, record.out_id or None)

    if not verified:
        return False

    record.is_used = True
    record.save(update_fields=['is_used'])
    return True
