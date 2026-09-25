"""Tag system serializers."""

from rest_framework import serializers

from tag_system.models import ProductTagConfig, Tag, TagCategory, TenantTagConfig


class TagCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TagCategory
        fields = ['id', 'name', 'code', 'category_type', 'sort_order', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class TagSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_type = serializers.CharField(source='category.category_type', read_only=True)

    class Meta:
        model = Tag
        fields = [
            'id', 'name', 'code', 'category', 'category_name', 'category_type',
            'color', 'text_color', 'icon', 'priority', 'is_active',
            'can_tenant_use', 'can_product_use', 'requires_approval', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class TenantTagConfigSerializer(serializers.ModelSerializer):
    tag_name = serializers.CharField(source='tag.name', read_only=True)
    tag_code = serializers.CharField(source='tag.code', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)

    class Meta:
        model = TenantTagConfig
        fields = [
            'id', 'tenant', 'tenant_name', 'tag', 'tag_name', 'tag_code',
            'is_participating', 'custom_name', 'rules', 'start_time', 'end_time',
            'status', 'reject_reason', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class ProductTagConfigSerializer(serializers.ModelSerializer):
    tag_name = serializers.CharField(source='tag.name', read_only=True)
    tag_code = serializers.CharField(source='tag.code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ProductTagConfig
        fields = [
            'id', 'product', 'product_name', 'tag', 'tag_name', 'tag_code',
            'is_active', 'display_text', 'source_type', 'start_time', 'end_time',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
