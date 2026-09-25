"""Mall customer auth serializers."""

from rest_framework import serializers

from customers.models import Customer, SmsVerificationCode
from customers.phone_utils import normalize_phone


class SendSmsSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    scene = serializers.ChoiceField(
        choices=[
            SmsVerificationCode.SCENE_REGISTER,
            SmsVerificationCode.SCENE_RESET_PASSWORD,
            SmsVerificationCode.SCENE_LOGIN,
        ],
    )

    def validate_phone(self, value: str) -> str:
        try:
            return normalize_phone(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc


class CustomerRegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    sms_code = serializers.CharField(max_length=8)
    password = serializers.CharField(min_length=8, max_length=128, write_only=True)
    nickname = serializers.CharField(max_length=64, required=False, allow_blank=True, default='')
    email = serializers.EmailField(required=False, allow_blank=True, default='')

    def validate_phone(self, value: str) -> str:
        try:
            phone = normalize_phone(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        if Customer.objects.filter(phone=phone).exists():
            raise serializers.ValidationError('该号码已注册')
        return phone


class CustomerLoginSerializer(serializers.Serializer):
    LOGIN_PHONE_PASSWORD = 'phone_password'
    LOGIN_PHONE_SMS = 'phone_sms'
    LOGIN_ACCOUNT_PASSWORD = 'account_password'

    login_mode = serializers.ChoiceField(
        choices=[LOGIN_PHONE_PASSWORD, LOGIN_PHONE_SMS, LOGIN_ACCOUNT_PASSWORD],
        default=LOGIN_ACCOUNT_PASSWORD,
    )
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True, default='')
    account = serializers.CharField(max_length=128, required=False, allow_blank=True, default='')
    password = serializers.CharField(max_length=128, required=False, allow_blank=True, default='')
    sms_code = serializers.CharField(max_length=8, required=False, allow_blank=True, default='')

    def validate(self, attrs):
        mode = attrs.get('login_mode')
        if mode in (self.LOGIN_PHONE_PASSWORD, self.LOGIN_PHONE_SMS):
            phone_raw = (attrs.get('phone') or '').strip()
            if not phone_raw:
                raise serializers.ValidationError({'phone': '请输入号码'})
            try:
                attrs['phone'] = normalize_phone(phone_raw)
            except ValueError as exc:
                raise serializers.ValidationError({'phone': str(exc)}) from exc
        if mode == self.LOGIN_PHONE_PASSWORD:
            if not attrs.get('password'):
                raise serializers.ValidationError({'password': '请输入密码'})
        elif mode == self.LOGIN_PHONE_SMS:
            if not (attrs.get('sms_code') or '').strip():
                raise serializers.ValidationError({'sms_code': '请输入验证码'})
            attrs['sms_code'] = attrs['sms_code'].strip()
        elif mode == self.LOGIN_ACCOUNT_PASSWORD:
            account = (attrs.get('account') or '').strip()
            if not account:
                raise serializers.ValidationError({'account': '请输入用户名或号码'})
            if not attrs.get('password'):
                raise serializers.ValidationError({'password': '请输入密码'})
            attrs['account'] = account
        return attrs


class CustomerResetPasswordSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    sms_code = serializers.CharField(max_length=8)
    password = serializers.CharField(min_length=8, max_length=128, write_only=True)

    def validate_phone(self, value: str) -> str:
        try:
            phone = normalize_phone(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        if not Customer.objects.filter(phone=phone).exists():
            raise serializers.ValidationError('该号码未注册')
        return phone
