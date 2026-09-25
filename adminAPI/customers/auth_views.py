"""Mall customer authentication API."""

import logging

from django.db import transaction
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from common.response import error_response, success_response
from customers.auth_utils import resolve_customer_by_account
from customers.auth_serializers import (
    CustomerLoginSerializer,
    CustomerRegisterSerializer,
    CustomerResetPasswordSerializer,
    SendSmsSerializer,
)
from customers.permissions import IsCustomerAuthenticated
from customers.models import Customer, SmsVerificationCode
from customers.serializers import CustomerProfileSerializer
from customers.sms_service import send_verification_code, verify_code
from customers.tokens import CustomerRefreshToken

logger = logging.getLogger(__name__)


def _issue_tokens(customer: Customer) -> dict:
    refresh = CustomerRefreshToken.for_customer(customer)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'customer': CustomerProfileSerializer(customer).data,
    }


class SendSmsView(APIView):
    """Send SMS verification code."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = SendSmsSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        phone = serializer.validated_data['phone']
        scene = serializer.validated_data['scene']
        if scene == SmsVerificationCode.SCENE_REGISTER and Customer.objects.filter(phone=phone).exists():
            return error_response('该号码已注册', code=40011)
        if scene in (
            SmsVerificationCode.SCENE_RESET_PASSWORD,
            SmsVerificationCode.SCENE_LOGIN,
        ) and not Customer.objects.filter(phone=phone).exists():
            return error_response('该号码未注册', code=40012)
        try:
            message, dev_code = send_verification_code(phone, scene)
        except ValueError as exc:
            msg = str(exc)
            if '频繁' in msg:
                return error_response(msg, code=40013)
            return error_response(msg, code=40014)
        except Exception:
            logger.exception('Send SMS failed: phone=%s scene=%s', phone, scene)
            return error_response('验证码发送失败', code=50010, http_status=500)
        data = {'dev_code': dev_code} if dev_code else None
        return success_response(data=data, message=message)


class CustomerRegisterView(APIView):
    """Register mall customer with phone + SMS code."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = CustomerRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        data = serializer.validated_data
        if not verify_code(data['phone'], SmsVerificationCode.SCENE_REGISTER, data['sms_code']):
            return error_response('验证码错误或已过期')
        nickname = (data.get('nickname') or '').strip() or f'用户{data["phone"][-4:]}'
        try:
            with transaction.atomic():
                customer = Customer(
                    phone=data['phone'],
                    nickname=nickname,
                    name=nickname,
                    email=(data.get('email') or '').strip(),
                    is_active=True,
                    tenant=getattr(request, 'tenant', None),
                )
                customer.set_password(data['password'])
                customer.save()
        except Exception:
            logger.exception('Customer register failed: phone=%s', data['phone'])
            return error_response('注册失败', code=50000, http_status=500)
        return success_response(data=_issue_tokens(customer), message='注册成功')


class CustomerLoginView(APIView):
    """Login mall customer: phone+password / phone+sms / account+password."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = CustomerLoginSerializer(data=request.data)
        if not serializer.is_valid():
            first = next(iter(serializer.errors.values()))
            message = first[0] if isinstance(first, list) else str(first)
            return error_response(str(message))
        data = serializer.validated_data
        mode = data['login_mode']

        if mode == CustomerLoginSerializer.LOGIN_PHONE_SMS:
            phone = data['phone']
            if not verify_code(phone, SmsVerificationCode.SCENE_LOGIN, data['sms_code']):
                return error_response('验证码错误或已过期')
            try:
                customer = Customer.objects.get(phone=phone)
            except Customer.DoesNotExist:
                return error_response('该号码未注册', code=40012)
        elif mode == CustomerLoginSerializer.LOGIN_PHONE_PASSWORD:
            try:
                customer = Customer.objects.get(phone=data['phone'])
            except Customer.DoesNotExist:
                return error_response('号码或密码错误', code=40002)
            if not customer.check_password(data['password']):
                return error_response('号码或密码错误', code=40002)
        else:
            customer = resolve_customer_by_account(data['account'])
            if customer is None:
                return error_response('用户名/号码或密码错误', code=40002)
            if not customer.check_password(data['password']):
                return error_response('用户名/号码或密码错误', code=40002)

        if not customer.is_active:
            return error_response('账号已被禁用', code=40003)
        return success_response(data=_issue_tokens(customer), message='登录成功')


class CustomerRefreshView(APIView):
    """Refresh mall customer access token."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return error_response('缺少 refresh token')
        try:
            refresh = RefreshToken(refresh_token)
        except (InvalidToken, TokenError):
            return error_response('登录已失效，请重新登录', code=40100, http_status=401)
        if refresh.get('token_type') != 'customer':
            return error_response('无效的商城令牌', code=40100, http_status=401)
        customer_id = refresh.get('customer_id')
        try:
            customer = Customer.objects.get(pk=customer_id, is_active=True)
        except Customer.DoesNotExist:
            return error_response('账号不存在或已被禁用', code=40100, http_status=401)
        new_refresh = CustomerRefreshToken.for_customer(customer)
        return success_response(
            data={
                'access': str(new_refresh.access_token),
                'refresh': str(new_refresh),
            },
        )


class CustomerResetPasswordView(APIView):
    """Reset password via SMS code."""

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = CustomerResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        data = serializer.validated_data
        if not verify_code(data['phone'], SmsVerificationCode.SCENE_RESET_PASSWORD, data['sms_code']):
            return error_response('验证码错误或已过期')
        try:
            customer = Customer.objects.get(phone=data['phone'])
            customer.set_password(data['password'])
            customer.save(update_fields=['password', 'updated_at'])
        except Customer.DoesNotExist:
            return error_response('该手机号未注册')
        return success_response(message='密码重置成功，请登录')


class CustomerProfileView(APIView):
    """Current mall customer profile."""

    permission_classes = [IsCustomerAuthenticated]

    def get(self, request: Request) -> Response:
        return success_response(data=CustomerProfileSerializer(request.customer).data)

    def patch(self, request: Request) -> Response:
        customer = request.customer
        allowed = {'nickname', 'email', 'avatar', 'real_name'}
        data = {k: v for k, v in request.data.items() if k in allowed}
        serializer = CustomerProfileSerializer(customer, data=data, partial=True)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        customer = serializer.save()
        if customer.nickname:
            customer.name = customer.nickname
            customer.save(update_fields=['name', 'updated_at'])
        return success_response(data=CustomerProfileSerializer(customer).data, message='更新成功')
