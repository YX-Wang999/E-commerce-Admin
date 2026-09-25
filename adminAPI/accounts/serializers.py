"""Account serializers."""

from django.contrib.auth import authenticate
from rest_framework import serializers

from accounts.activation import get_activation_display_status
from accounts.models import ActivationLog, Department, User
from rbac.models import Role
from rbac.serializers import RoleListSerializer


class UserSerializer(serializers.ModelSerializer):
    """User read serializer."""

    roles = RoleListSerializer(many=True, read_only=True)
    role_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Role.objects.all(),
        source='roles',
        write_only=True,
        required=False,
    )
    activation_status = serializers.SerializerMethodField()
    activation_status_label = serializers.SerializerMethodField()
    last_activation_sent_at = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    managed_department_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'nickname',
            'email',
            'phone',
            'avatar',
            'is_active',
            'is_first_login',
            'is_superuser',
            'department',
            'department_name',
            'managed_department_name',
            'roles',
            'role_ids',
            'activation_status',
            'activation_status_label',
            'last_activation_sent_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'is_superuser', 'created_at', 'updated_at']

    def get_department_name(self, obj: User) -> str:
        """Return belonging department name."""
        if obj.department_id is None:
            return ''
        return obj.department.name

    def get_managed_department_name(self, obj: User) -> str:
        """Return managed department name if user is a department manager."""
        managed = obj.managed_department
        return managed.name if managed else ''

    def _get_latest_activation_log(self, obj: User) -> ActivationLog | None:
        """Get latest activation log for user."""
        prefetched = getattr(obj, '_prefetched_objects_cache', {}).get('activation_logs')
        if prefetched is not None:
            return prefetched[0] if prefetched else None
        return obj.activation_logs.order_by('-sent_at').first()

    def get_activation_status(self, obj: User) -> str:
        """Return latest activation status code."""
        log = self._get_latest_activation_log(obj)
        status_code, _ = get_activation_display_status(log)
        return status_code

    def get_activation_status_label(self, obj: User) -> str:
        """Return latest activation status label."""
        log = self._get_latest_activation_log(obj)
        _, status_label = get_activation_display_status(log)
        return status_label

    def get_last_activation_sent_at(self, obj: User) -> str | None:
        """Return latest activation email sent time."""
        log = self._get_latest_activation_log(obj)
        if log is None:
            return None
        return log.sent_at.isoformat()


class UserCreateSerializer(serializers.ModelSerializer):
    """User create serializer."""

    password = serializers.CharField(write_only=True, min_length=6)
    role_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Role.objects.all(),
        source='roles',
        required=False,
    )
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.filter(is_active=True),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'password',
            'nickname',
            'email',
            'phone',
            'avatar',
            'is_active',
            'department',
            'role_ids',
        ]
        read_only_fields = ['id']

    def create(self, validated_data: dict) -> User:
        """Create user with hashed password."""
        roles = validated_data.pop('roles', [])
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        if roles:
            user.roles.set(roles)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """User update serializer."""

    password = serializers.CharField(write_only=True, min_length=6, required=False)
    role_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Role.objects.all(),
        source='roles',
        required=False,
    )
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = User
        fields = [
            'nickname',
            'email',
            'phone',
            'avatar',
            'is_active',
            'password',
            'department',
            'role_ids',
        ]

    def update(self, instance: User, validated_data: dict) -> User:
        """Update user fields."""
        roles = validated_data.pop('roles', None)
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        if roles is not None:
            instance.roles.set(roles)
        return instance


class LoginSerializer(serializers.Serializer):
    """Login request serializer."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        """Validate credentials."""
        username = attrs.get('username')
        password = attrs.get('password')
        user = authenticate(
            username=username,
            password=password,
        )
        if user is None:
            raise serializers.ValidationError('用户名或密码错误')
        if not user.is_active:
            raise serializers.ValidationError('账号已被禁用')
        attrs['user'] = user
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    """Admin reset user password serializer."""

    new_password = serializers.CharField(write_only=True, min_length=6)


class ChangePasswordSerializer(serializers.Serializer):
    """Current user change password serializer."""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate_old_password(self, value: str) -> str:
        """Validate old password matches current user."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('旧密码不正确')
        return value

    def validate(self, attrs: dict) -> dict:
        """Validate new password differs from old password."""
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({'new_password': '新密码不能与旧密码相同'})
        return attrs


class ActivateAccountSerializer(serializers.Serializer):
    """Employee account activation / password reset serializer."""

    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=6)
    mode = serializers.ChoiceField(
        choices=['activation', 'reset_password'],
        default='activation',
        required=False,
    )


class ForgotPasswordSerializer(serializers.Serializer):
    """Forgot password email request serializer."""

    email = serializers.EmailField()


class RegisterSerializer(serializers.Serializer):
    """Mall user self-registration serializer."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate_username(self, value: str) -> str:
        """Ensure username is unique."""
        username = value.strip()
        if not username:
            raise serializers.ValidationError('请输入用户名')
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError('用户名已被使用')
        return username

    def validate_email(self, value: str) -> str:
        """Ensure email is unique."""
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('邮箱已被注册')
        return email

    def validate(self, attrs: dict) -> dict:
        """Ensure passwords match."""
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': '两次密码不一致'})
        return attrs
