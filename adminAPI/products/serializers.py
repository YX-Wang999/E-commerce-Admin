"""Product serializers."""

from django.conf import settings
from rest_framework import serializers

from common.media_utils import append_cache_version, strip_url_query, to_relative_media_url
from products.models import Brand, Category, InventoryLog, Product
from products.category_utils import (
    MAX_CATEGORY_DEPTH,
    get_category_full_path,
    get_category_level,
    validate_parent_assignment,
)


class CategorySerializer(serializers.ModelSerializer):
    """Category CRUD serializer."""

    level = serializers.SerializerMethodField()
    full_path = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'parent', 'parent_name', 'name', 'icon', 'sort_order', 'is_active',
            'level', 'full_path', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'level', 'full_path', 'parent_name', 'created_at', 'updated_at']

    def get_level(self, obj: Category) -> int:
        return get_category_level(obj)

    def get_full_path(self, obj: Category) -> str:
        return get_category_full_path(obj)

    def get_parent_name(self, obj: Category) -> str:
        return obj.parent.name if obj.parent_id else ''

    def validate(self, attrs: dict) -> dict:
        if 'parent' in attrs:
            parent = attrs['parent']
        elif self.instance:
            parent = self.instance.parent
        else:
            parent = None
        error = validate_parent_assignment(self.instance, parent)
        if error:
            raise serializers.ValidationError({'parent': error})
        return attrs


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Recursive category tree serializer."""

    children = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    full_path = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'icon', 'sort_order', 'is_active',
            'level', 'full_path', 'parent', 'parent_name', 'children',
        ]

    def get_level(self, obj: Category) -> int:
        return get_category_level(obj)

    def get_full_path(self, obj: Category) -> str:
        return get_category_full_path(obj)

    def get_parent_name(self, obj: Category) -> str:
        return obj.parent.name if obj.parent_id else ''

    def get_children(self, obj: Category) -> list:
        depth = self.context.get('depth', 0)
        if depth >= MAX_CATEGORY_DEPTH - 1:
            return []
        prefetched = getattr(obj, '_prefetched_children', None)
        active_only = self.context.get('active_only', False)
        if prefetched is not None:
            children = list(prefetched)
            if active_only:
                children = [item for item in children if item.is_active]
        else:
            children = list(obj.children.order_by('sort_order', 'id'))
            if active_only:
                children = [item for item in children if item.is_active]
        return CategoryTreeSerializer(
            children,
            many=True,
            context={**self.context, 'depth': depth + 1},
        ).data


class CategoryFlatSerializer(serializers.ModelSerializer):
    """Flat category list for parent selectors."""

    level = serializers.SerializerMethodField()
    full_path = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'parent', 'parent_name', 'name', 'icon', 'sort_order',
            'is_active', 'level', 'full_path',
        ]

    def get_level(self, obj: Category) -> int:
        return get_category_level(obj)

    def get_full_path(self, obj: Category) -> str:
        return get_category_full_path(obj)

    def get_parent_name(self, obj: Category) -> str:
        return obj.parent.name if obj.parent_id else '-'


class BrandSerializer(serializers.ModelSerializer):
    """Brand serializer with logo file path and external URL support."""

    logo = serializers.CharField(required=False, allow_blank=True, write_only=True)
    logo_display = serializers.CharField(read_only=True)

    class Meta:
        model = Brand
        fields = [
            'id', 'name', 'logo', 'logo_url', 'logo_display',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'logo_display', 'created_at', 'updated_at']

    def _normalize_media_path(self, value: str) -> str:
        """Convert API URL to storage-relative path."""
        if not value:
            return ''
        media_url = settings.MEDIA_URL.rstrip('/')
        if value.startswith('http://') or value.startswith('https://'):
            if '/media/' in value:
                return value.split('/media/', 1)[1]
            return ''
        if value.startswith(f'{media_url}/'):
            return value[len(media_url) + 1:]
        return value.lstrip('/')

    def _apply_logo(self, instance: Brand, logo_value: str | None) -> None:
        """Apply uploaded logo path to model instance."""
        if logo_value is None:
            return
        normalized = self._normalize_media_path(logo_value)
        if normalized:
            instance.logo.name = normalized
        else:
            instance.logo = None

    def to_representation(self, instance: Brand) -> dict:
        """Serialize brand with logo_display and writable logo path."""
        data = super().to_representation(instance)
        data['logo'] = instance.logo.url if instance.logo else ''
        data['logo_display'] = instance.logo_display
        return data

    def create(self, validated_data: dict) -> Brand:
        """Create brand with optional uploaded logo."""
        logo_value = validated_data.pop('logo', '')
        if validated_data.get('logo_url') == '':
            validated_data['logo_url'] = None
        instance = Brand.objects.create(**validated_data)
        self._apply_logo(instance, logo_value)
        instance.save(update_fields=['logo'])
        return instance

    def update(self, instance: Brand, validated_data: dict) -> Brand:
        """Update brand with optional uploaded logo."""
        logo_value = validated_data.pop('logo', None)
        if validated_data.get('logo_url') == '':
            validated_data['logo_url'] = None
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        self._apply_logo(instance, logo_value)
        instance.save()
        return instance


class TenantBriefSerializer(serializers.Serializer):
    """Nested tenant info on product detail."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    code = serializers.CharField()
    status = serializers.CharField()
    logo = serializers.CharField(allow_null=True, allow_blank=True)
    intro = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()
    rating_label = serializers.SerializerMethodField()
    quality_score = serializers.SerializerMethodField()
    service_score = serializers.SerializerMethodField()
    logistics_score = serializers.SerializerMethodField()
    sold_count = serializers.SerializerMethodField()
    follower_count = serializers.SerializerMethodField()
    closure_state = serializers.SerializerMethodField()
    closure_notice_end_at = serializers.SerializerMethodField()

    def get_closure_state(self, obj) -> str:
        from shop_closure.services import tenant_closure_state

        return tenant_closure_state(obj)['state']

    def get_closure_notice_end_at(self, obj) -> str | None:
        from shop_closure.services import tenant_closure_state

        return tenant_closure_state(obj)['notice_end_at']

    def get_follower_count(self, obj) -> int:
        config = getattr(obj, 'config', None) or {}
        try:
            return int(config.get('follower_count', 0) or 0)
        except (TypeError, ValueError):
            return 0

    def get_intro(self, obj) -> str:
        config = getattr(obj, 'config', None) or {}
        return str(config.get('intro') or getattr(obj, 'address', '') or '')

    def get_rating(self, obj) -> float:
        from shop_rating.services import get_tenant_rating_display

        return get_tenant_rating_display(obj.id)['overall_score']

    def get_rating_count(self, obj) -> int:
        from shop_rating.services import get_tenant_rating_display

        return get_tenant_rating_display(obj.id)['total_ratings']

    def get_rating_label(self, obj) -> str:
        from shop_rating.services import get_tenant_rating_display

        return get_tenant_rating_display(obj.id)['rating_label']

    def get_quality_score(self, obj) -> float:
        from shop_rating.services import get_tenant_rating_display

        return get_tenant_rating_display(obj.id)['quality_score']

    def get_service_score(self, obj) -> float:
        from shop_rating.services import get_tenant_rating_display

        return get_tenant_rating_display(obj.id)['service_score']

    def get_logistics_score(self, obj) -> float:
        from shop_rating.services import get_tenant_rating_display

        return get_tenant_rating_display(obj.id)['logistics_score']

    def get_sold_count(self, obj) -> int:
        from django.db.models import Sum

        from orders.models import Order, OrderItem

        total = OrderItem.objects.filter(
            product__tenant_id=obj.id,
            order__status__in=[
                Order.STATUS_PAID,
                Order.STATUS_SHIPPED,
                Order.STATUS_COMPLETED,
            ],
        ).aggregate(total=Sum('quantity'))['total']
        return int(total or 0)


class ProductSimpleSerializer(serializers.ModelSerializer):
    """Minimal product fields for cart and lists."""

    tenant_name = serializers.CharField(source='tenant.name', read_only=True, allow_null=True)
    tenant_code = serializers.CharField(source='tenant.code', read_only=True, allow_null=True)
    tenant_logo = serializers.SerializerMethodField()
    tenant_rating = serializers.SerializerMethodField()
    promo_tags = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'stock', 'image', 'status',
            'tenant', 'tenant_name', 'tenant_code', 'tenant_logo', 'tenant_rating', 'promo_tags',
        ]
        read_only_fields = fields

    def get_tenant_logo(self, obj: Product) -> str:
        if obj.tenant_id and obj.tenant.logo:
            return str(obj.tenant.logo)
        return ''

    def get_tenant_rating(self, obj: Product):
        if not obj.tenant_id:
            return None
        from shop_rating.services import get_tenant_rating_display

        return get_tenant_rating_display(obj.tenant_id)['overall_score']

    def get_promo_tags(self, obj: Product) -> list:
        from tag_system.services import get_display_tags_for_product

        return get_display_tags_for_product(obj, limit=3)

    def to_representation(self, instance: Product) -> dict:
        data = super().to_representation(instance)
        data['image'] = to_relative_media_url(
            instance.image.url if instance.image else '',
            instance.updated_at.timestamp(),
        )
        return data


class ProductSerializer(serializers.ModelSerializer):
    """Product serializer with image path read/write support."""

    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True, allow_null=True)
    tenant_code = serializers.CharField(source='tenant.code', read_only=True, allow_null=True)
    tenant_logo = serializers.SerializerMethodField()
    promo_tags = serializers.SerializerMethodField()
    tenant_rating = serializers.SerializerMethodField()
    sold_count = serializers.SerializerMethodField()
    image = serializers.CharField(required=False, allow_blank=True)
    gallery = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'category_name', 'brand', 'brand_name',
            'tenant', 'tenant_name', 'tenant_code', 'tenant_logo', 'tenant_rating', 'promo_tags',
            'price', 'stock', 'description', 'image', 'gallery', 'status', 'is_active',
            'sold_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_tenant_logo(self, obj: Product) -> str:
        if obj.tenant_id and obj.tenant.logo:
            return str(obj.tenant.logo)
        return ''

    def get_tenant_rating(self, obj: Product):
        if not obj.tenant_id:
            return None
        from shop_rating.services import get_tenant_rating_display

        return get_tenant_rating_display(obj.tenant_id)['overall_score']

    def get_promo_tags(self, obj: Product) -> list:
        from tag_system.services import get_display_tags_for_product

        return get_display_tags_for_product(obj, limit=3)

    def get_sold_count(self, obj: Product) -> int:
        annotated = getattr(obj, 'sold_count', None)
        if annotated is not None:
            return int(annotated)
        from django.db.models import Sum

        from orders.models import Order, OrderItem

        total = OrderItem.objects.filter(
            product_id=obj.id,
            order__status__in=[
                Order.STATUS_PAID,
                Order.STATUS_SHIPPED,
                Order.STATUS_COMPLETED,
            ],
        ).aggregate(total=Sum('quantity'))['total']
        return int(total or 0)

    def _normalize_image_path(self, value: str) -> str:
        """Convert API URL to storage-relative path."""
        value = strip_url_query(value)
        if not value:
            return ''
        media_url = settings.MEDIA_URL.rstrip('/')
        if value.startswith('http://') or value.startswith('https://'):
            if '/media/' in value:
                return value.split('/media/', 1)[1]
            return value
        if value.startswith(f'{media_url}/'):
            return value[len(media_url) + 1:]
        return value.lstrip('/')

    def _build_image_url(self, instance: Product) -> str:
        """Build image URL for API response."""
        if not instance.image:
            return ''
        return to_relative_media_url(
            instance.image.url,
            instance.updated_at.timestamp(),
        )

    def _build_gallery_urls(self, gallery: list | None, version) -> list[str]:
        """Normalize gallery paths to public /media/ URLs."""
        results = []
        for item in gallery or []:
            item = strip_url_query(item)
            if not item:
                continue
            results.append(to_relative_media_url(item, version))
        return results

    def to_representation(self, instance: Product) -> dict:
        data = super().to_representation(instance)
        data['image'] = self._build_image_url(instance)
        data['gallery'] = self._build_gallery_urls(instance.gallery, instance.updated_at.timestamp())
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        customer = getattr(request, 'customer', None) if request else None
        is_platform_staff = (
            user
            and user.is_authenticated
            and hasattr(user, 'roles')
            and customer is None
        )
        if instance.tenant_id and not is_platform_staff:
            data['tenant'] = TenantBriefSerializer(instance.tenant).data
        elif not instance.tenant_id:
            data['tenant'] = None
        return data

    def _apply_image(self, instance: Product, image_value: str | None) -> None:
        """Apply image path to model instance."""
        if image_value is None:
            return
        normalized = self._normalize_image_path(image_value)
        if normalized:
            instance.image.name = normalized
        else:
            instance.image = None

    def _normalize_gallery_for_storage(self, gallery: list | None) -> list[str]:
        return [strip_url_query(item) for item in (gallery or []) if strip_url_query(item)]

    def create(self, validated_data: dict) -> Product:
        """Create product with optional image path."""
        image_value = validated_data.pop('image', '')
        gallery = self._normalize_gallery_for_storage(validated_data.pop('gallery', []))
        instance = Product.objects.create(**validated_data, gallery=gallery)
        self._apply_image(instance, image_value)
        instance.save(update_fields=['image'])
        return instance

    def update(self, instance: Product, validated_data: dict) -> Product:
        """Update product with optional image path."""
        image_value = validated_data.pop('image', None)
        if 'gallery' in validated_data:
            instance.gallery = self._normalize_gallery_for_storage(validated_data.pop('gallery'))
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        self._apply_image(instance, image_value)
        instance.save()
        return instance


class InventoryLogSerializer(serializers.ModelSerializer):
    """Inventory log read serializer."""

    product_name = serializers.CharField(source='product.name', read_only=True)
    change_type_label = serializers.CharField(source='get_change_type_display', read_only=True)
    changed_by_name = serializers.SerializerMethodField()
    order_no = serializers.CharField(source='order.order_no', read_only=True, default='')

    class Meta:
        model = InventoryLog
        fields = [
            'id', 'product', 'product_name', 'change_type', 'change_type_label',
            'before_quantity', 'after_quantity', 'changed_by', 'changed_by_name',
            'order', 'order_no', 'remark', 'created_at',
        ]
        read_only_fields = fields

    def get_changed_by_name(self, obj: InventoryLog) -> str:
        """Return operator display name."""
        if not obj.changed_by:
            return '-'
        return obj.changed_by.nickname or obj.changed_by.username
