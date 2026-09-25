"""RBAC serializers."""

from rest_framework import serializers

from rbac.models import Menu, Permission, Role


class PermissionSerializer(serializers.ModelSerializer):
    """Permission serializer."""

    class Meta:
        model = Permission
        fields = [
            'id',
            'name',
            'code',
            'module',
            'action',
            'description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MenuSerializer(serializers.ModelSerializer):
    """Menu serializer."""

    permission_code = serializers.CharField(
        source='permission.code',
        read_only=True,
        default='',
    )

    class Meta:
        model = Menu
        fields = [
            'id',
            'parent',
            'title',
            'name',
            'path',
            'component',
            'icon',
            'menu_type',
            'permission',
            'permission_code',
            'sort_order',
            'is_visible',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MenuTreeSerializer(serializers.ModelSerializer):
    """Menu tree node serializer."""

    class Meta:
        model = Menu
        fields = [
            'id',
            'title',
            'name',
            'path',
            'component',
            'icon',
            'menu_type',
            'sort_order',
        ]


class RoleListSerializer(serializers.ModelSerializer):
    """Role list serializer."""

    class Meta:
        model = Role
        fields = ['id', 'name', 'code', 'description', 'is_active']


class RoleSerializer(serializers.ModelSerializer):
    """Role detail serializer."""

    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        source='permissions',
        required=False,
    )
    menu_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Menu.objects.all(),
        source='menus',
        required=False,
    )
    permissions = PermissionSerializer(many=True, read_only=True)
    menus = MenuSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = [
            'id',
            'name',
            'code',
            'description',
            'is_active',
            'permissions',
            'menus',
            'permission_ids',
            'menu_ids',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
