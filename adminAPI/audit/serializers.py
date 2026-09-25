"""Audit serializers."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from audit.models import OperationLog
from system.role_display_names import resolve_role_name

User = get_user_model()


class OperationLogSerializer(serializers.ModelSerializer):
    """Operation log serializer."""

    user_role_codes = serializers.SerializerMethodField()
    user_role_labels = serializers.SerializerMethodField()

    class Meta:
        model = OperationLog
        fields = [
            'id',
            'user',
            'username',
            'user_role_codes',
            'user_role_labels',
            'module',
            'action',
            'resource',
            'resource_id',
            'detail',
            'ip',
            'user_agent',
            'request_method',
            'request_path',
            'created_at',
        ]
        read_only_fields = fields

    def _user_roles(self, obj: OperationLog) -> list:
        cache = self.context.setdefault('_user_roles_cache', {})
        if obj.user_id in cache:
            return cache[obj.user_id]
        if not obj.user_id:
            cache[obj.user_id] = []
            return []
        user = User.objects.filter(pk=obj.user_id).prefetch_related('roles').first()
        roles = list(user.roles.filter(is_active=True)) if user else []
        cache[obj.user_id] = roles
        return roles

    def get_user_role_codes(self, obj: OperationLog) -> list[str]:
        return [role.code for role in self._user_roles(obj)]

    def get_user_role_labels(self, obj: OperationLog) -> str:
        locale = self.context.get('locale', 'zh-CN')
        labels = [
            resolve_role_name(role.code, locale, role.name)
            for role in self._user_roles(obj)
        ]
        return '、'.join(labels) if labels else ''
