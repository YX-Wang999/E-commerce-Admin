"""Announcement serializers."""

from django.utils import timezone
from rest_framework import serializers

from accounts.models import Department
from announcement.models import Announcement
from rbac.models import Role


class AnnouncementSerializer(serializers.ModelSerializer):
    """Announcement read serializer."""

    type = serializers.CharField(source='announce_type', read_only=True)
    type_label = serializers.CharField(source='get_announce_type_display', read_only=True)
    priority_label = serializers.CharField(source='get_priority_display', read_only=True)
    scope_label = serializers.CharField(source='get_scope_display', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    publisher_name = serializers.SerializerMethodField()
    target_role_ids = serializers.PrimaryKeyRelatedField(
        source='target_roles',
        many=True,
        read_only=True,
    )
    target_department_ids = serializers.PrimaryKeyRelatedField(
        source='target_departments',
        many=True,
        read_only=True,
    )

    class Meta:
        model = Announcement
        fields = [
            'id',
            'title',
            'content',
            'type',
            'type_label',
            'announce_type',
            'priority',
            'priority_label',
            'scope',
            'scope_label',
            'target_role_ids',
            'target_department_ids',
            'is_pinned',
            'effective_at',
            'expires_at',
            'status',
            'status_label',
            'publisher',
            'publisher_name',
            'published_at',
            'created_at',
        ]

    def get_publisher_name(self, obj: Announcement) -> str:
        """Return publisher display name."""
        if obj.publisher_id is None:
            return ''
        return obj.publisher.nickname or obj.publisher.username


class AnnouncementWriteSerializer(serializers.ModelSerializer):
    """Announcement create/update serializer."""

    type = serializers.ChoiceField(
        source='announce_type',
        choices=Announcement.TYPE_CHOICES,
        write_only=True,
    )
    target_role_ids = serializers.PrimaryKeyRelatedField(
        source='target_roles',
        queryset=Role.objects.filter(is_active=True),
        many=True,
        required=False,
    )
    target_department_ids = serializers.PrimaryKeyRelatedField(
        source='target_departments',
        queryset=Department.objects.filter(is_active=True),
        many=True,
        required=False,
    )

    class Meta:
        model = Announcement
        fields = [
            'title',
            'content',
            'type',
            'priority',
            'scope',
            'target_role_ids',
            'target_department_ids',
            'is_pinned',
            'effective_at',
            'expires_at',
            'status',
        ]

    def validate(self, attrs: dict) -> dict:
        """Validate scope targets and time range."""
        effective_at = attrs.get('effective_at')
        expires_at = attrs.get('expires_at')
        if effective_at and expires_at and effective_at >= expires_at:
            raise serializers.ValidationError('失效时间必须晚于生效时间')

        scope = attrs.get('scope')
        target_roles = attrs.get('target_roles')
        target_departments = attrs.get('target_departments')
        if scope == Announcement.SCOPE_ROLE and not target_roles:
            raise serializers.ValidationError('指定角色时必须选择至少一个角色')
        if scope == Announcement.SCOPE_DEPARTMENT and not target_departments:
            raise serializers.ValidationError('指定部门时必须选择至少一个部门')
        return attrs

    def create(self, validated_data: dict) -> Announcement:
        """Create announcement with M2M relations."""
        target_roles = validated_data.pop('target_roles', [])
        target_departments = validated_data.pop('target_departments', [])
        if validated_data.get('status') != Announcement.STATUS_PUBLISHED:
            validated_data['status'] = Announcement.STATUS_DRAFT
        else:
            request = self.context.get('request')
            validated_data['published_at'] = timezone.now()
            if request and getattr(request.user, 'is_authenticated', False):
                validated_data['publisher'] = request.user
        instance = Announcement.objects.create(**validated_data)
        if target_roles:
            instance.target_roles.set(target_roles)
        if target_departments:
            instance.target_departments.set(target_departments)
        return instance

    def update(self, instance: Announcement, validated_data: dict) -> Announcement:
        """Update announcement with M2M relations."""
        target_roles = validated_data.pop('target_roles', None)
        target_departments = validated_data.pop('target_departments', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if target_roles is not None:
            instance.target_roles.set(target_roles)
        if target_departments is not None:
            instance.target_departments.set(target_departments)
        return instance


class AnnouncementPublicSerializer(serializers.ModelSerializer):
    """Compact serializer for banner and dashboard."""

    type = serializers.CharField(source='announce_type', read_only=True)
    type_label = serializers.CharField(source='get_announce_type_display', read_only=True)
    priority_label = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = Announcement
        fields = [
            'id',
            'title',
            'content',
            'type',
            'type_label',
            'priority',
            'priority_label',
            'is_pinned',
            'effective_at',
            'expires_at',
            'published_at',
        ]
