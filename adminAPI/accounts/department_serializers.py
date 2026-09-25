"""Department serializers."""

from rest_framework import serializers

from accounts.models import Department, User


class DepartmentListSerializer(serializers.ModelSerializer):
    """Department read serializer for tree and flat lists."""

    parent = serializers.PrimaryKeyRelatedField(read_only=True)
    manager_name = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            'id',
            'name',
            'code',
            'parent',
            'manager',
            'manager_name',
            'member_count',
            'is_active',
            'created_at',
        ]
        read_only_fields = fields

    def get_manager_name(self, obj: Department) -> str:
        """Return manager display name."""
        if obj.manager_id is None:
            return ''
        return obj.manager.nickname or obj.manager.username

    def get_member_count(self, obj: Department) -> int:
        """Return active member count."""
        return obj.members.filter(is_active=True).count()


class DepartmentWriteSerializer(serializers.ModelSerializer):
    """Department create/update serializer."""

    parent = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        allow_null=True,
        required=False,
    )
    manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Department
        fields = [
            'id',
            'name',
            'code',
            'parent',
            'manager',
            'is_active',
        ]
        read_only_fields = ['id']

    def validate(self, attrs: dict) -> dict:
        """Prevent circular parent references."""
        parent = attrs.get('parent', getattr(self.instance, 'parent', None))
        instance = self.instance
        if parent and instance and parent.pk == instance.pk:
            raise serializers.ValidationError({'parent': '上级部门不能是自身'})
        if parent and instance:
            cursor = parent
            while cursor is not None:
                if cursor.pk == instance.pk:
                    raise serializers.ValidationError({'parent': '上级部门不能是当前部门的子部门'})
                cursor = cursor.parent
        return attrs
