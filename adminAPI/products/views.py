"""Product views."""

import logging
from datetime import datetime, time, timedelta

from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from common.pagination import StandardPagination
from common.response import error_response, success_response
from common.tenant import TenantViewSetMixin
from products.inventory import set_inventory_context
from products.category_utils import (
    CACHE_KEY_TREE,
    CACHE_TIMEOUT,
    count_children,
    count_products_in_subtree,
    get_category_children_ids,
    invalidate_category_cache,
)
from products.models import Brand, Category, InventoryLog, Product
from tenants.models import Tenant
from products.permissions import CanManageCategory, CanViewInventoryLog
from products.serializers import (
    BrandSerializer,
    CategoryFlatSerializer,
    CategorySerializer,
    CategoryTreeSerializer,
    InventoryLogSerializer,
    ProductSerializer,
)
from tag_system.services import attach_product_tags

logger = logging.getLogger(__name__)


class _BaseModelViewSet(viewsets.ModelViewSet):
    """Base viewset with unified responses."""

    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def list(self, request: Request, *args, **kwargs) -> Response:
        """List records."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        """Retrieve record."""
        return success_response(data=self.get_serializer(self.get_object()).data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create record."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Create failed')
            return error_response('创建失败', code=50000, http_status=500)
        return success_response(
            data=self.get_serializer(instance).data,
            message='创建成功',
            http_status=status.HTTP_201_CREATED,
        )

    def update(self, request: Request, *args, **kwargs) -> Response:
        """Update record."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Update failed')
            return error_response('更新失败', code=50000, http_status=500)
        return success_response(data=self.get_serializer(instance).data, message='更新成功')

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Delete record."""
        try:
            self.get_object().delete()
        except Exception:
            logger.exception('Delete failed')
            return error_response('删除失败', code=50000, http_status=500)
        return success_response(message='删除成功')


class CategoryViewSet(_BaseModelViewSet):
    """Category CRUD with tree endpoints."""

    queryset = Category.objects.select_related('parent').all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'tree', 'flat']:
            return [AllowAny()]
        return [IsAuthenticated(), CanManageCategory()]

    def _prefetch_tree_children(self, queryset):
        return queryset.prefetch_related(
            'children__children__children__children__children',
        )

    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request: Request) -> Response:
        """Return full category tree."""
        active_only = request.query_params.get('active_only', 'false').lower() in ('1', 'true')
        cache_key = f'{CACHE_KEY_TREE}:{"active" if active_only else "all"}'
        cached = cache.get(cache_key)
        if cached is not None:
            return success_response(data=cached)
        roots = self._prefetch_tree_children(
            Category.objects.filter(parent__isnull=True).order_by('sort_order', 'id'),
        )
        if active_only:
            roots = roots.filter(is_active=True)
        for root in roots:
            self._attach_prefetched_children(root)
        data = CategoryTreeSerializer(
            roots,
            many=True,
            context={'active_only': active_only},
        ).data
        cache.set(cache_key, data, CACHE_TIMEOUT)
        return success_response(data=data)

    def _attach_prefetched_children(self, node: Category) -> None:
        children = list(node.children.all())
        node._prefetched_children = children
        for child in children:
            self._attach_prefetched_children(child)

    @action(detail=False, methods=['get'], url_path='flat')
    def flat(self, request: Request) -> Response:
        """Return flat category list for parent selectors."""
        queryset = Category.objects.select_related('parent').order_by('sort_order', 'id')
        active_only = request.query_params.get('active_only', 'false').lower() in ('1', 'true')
        if active_only:
            queryset = queryset.filter(is_active=True)
        serializer = CategoryFlatSerializer(queryset, many=True)
        return success_response(data=serializer.data)

    @action(detail=False, methods=['post'], url_path='batch-sort')
    def batch_sort(self, request: Request) -> Response:
        """Batch update sort order for categories."""
        items = request.data.get('items') or []
        if not isinstance(items, list) or not items:
            return error_response('请提供排序数据')
        try:
            for item in items:
                category_id = item.get('id')
                sort_order = item.get('sort_order')
                if category_id is None or sort_order is None:
                    continue
                Category.objects.filter(pk=category_id).update(sort_order=sort_order)
        except Exception:
            logger.exception('Batch sort failed')
            return error_response('批量排序失败', code=50000, http_status=500)
        invalidate_category_cache()
        return success_response(message='排序已更新')

    def create(self, request: Request, *args, **kwargs) -> Response:
        response = super().create(request, *args, **kwargs)
        invalidate_category_cache()
        return response

    def update(self, request: Request, *args, **kwargs) -> Response:
        response = super().update(request, *args, **kwargs)
        invalidate_category_cache()
        return response

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        cascade = (
            request.query_params.get('cascade') in ('1', 'true', 'True')
            or request.data.get('cascade') in (True, 'true', '1', 1)
        )
        child_count = count_children(instance)
        product_count = count_products_in_subtree(instance)

        if child_count and not cascade:
            return error_response(f'该分类下有 {child_count} 个子分类，请先移动或删除子分类')
        if product_count:
            return error_response(f'该分类下有 {product_count} 个商品，请先转移商品')

        try:
            instance.delete()
        except Exception:
            logger.exception('Delete failed')
            return error_response('删除失败', code=50000, http_status=500)
        invalidate_category_cache()
        return success_response(message='删除成功')


class BrandViewSet(_BaseModelViewSet):
    """Brand CRUD."""

    queryset = Brand.objects.all()
    serializer_class = BrandSerializer


class InventoryLogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Inventory log list API."""

    serializer_class = InventoryLogSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated, CanViewInventoryLog]

    def get_queryset(self):
        """Filter inventory logs."""
        queryset = InventoryLog.objects.select_related(
            'product', 'changed_by', 'order',
        ).all()
        product_id = self.request.query_params.get('product_id')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if start_date:
            parsed_start = parse_date(start_date)
            if parsed_start:
                start_dt = timezone.make_aware(datetime.combine(parsed_start, time.min))
                queryset = queryset.filter(created_at__gte=start_dt)
        if end_date:
            parsed_end = parse_date(end_date)
            if parsed_end:
                end_dt = timezone.make_aware(datetime.combine(parsed_end, time.max))
                queryset = queryset.filter(created_at__lte=end_dt)
        return queryset.order_by('-created_at')

    def list(self, request: Request, *args, **kwargs) -> Response:
        """List inventory logs."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)


class ProductViewSet(TenantViewSetMixin, _BaseModelViewSet):
    """Product CRUD with on/off sale actions."""

    queryset = Product.objects.select_related('category', 'brand', 'tenant').all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_context(self) -> dict:
        """Pass request for absolute image URLs."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def _is_platform_staff(self) -> bool:
        user = self.request.user
        customer = getattr(self.request, 'customer', None)
        return (
            user.is_authenticated
            and hasattr(user, 'roles')
            and customer is None
        )

    def get_queryset(self):
        """Filter products by query params."""
        if self.action in ('list', 'retrieve') and not self._is_platform_staff():
            tenant = getattr(self.request, 'tenant', None)
            queryset = Product.objects.select_related('category', 'brand', 'tenant').filter(is_active=True)
            tenant_id = self.request.query_params.get('tenant_id')
            tenant_code = self.request.query_params.get('tenant_code')
            if tenant_id:
                try:
                    queryset = queryset.filter(tenant_id=int(tenant_id))
                except (TypeError, ValueError):
                    queryset = queryset.none()
            elif tenant_code:
                queryset = queryset.filter(
                    tenant__code=tenant_code,
                    tenant__status=Tenant.STATUS_ACTIVE,
                    tenant__is_active=True,
                )
            elif tenant is not None:
                queryset = queryset.filter(tenant=tenant)
            else:
                queryset = queryset.filter(
                    Q(tenant__isnull=True)
                    | Q(tenant__status=Tenant.STATUS_ACTIVE, tenant__is_active=True),
                )
            if not self.request.query_params.get('status'):
                queryset = queryset.filter(status=Product.STATUS_ON_SALE)
        else:
            queryset = super().get_queryset()
            if self.action in ('list', 'retrieve') and not self._is_platform_staff():
                queryset = queryset.filter(is_active=True)
                if not self.request.query_params.get('status'):
                    queryset = queryset.filter(status=Product.STATUS_ON_SALE)

        status_param = self.request.query_params.get('status')
        category_id = self.request.query_params.get('category')
        keyword = self.request.query_params.get('keyword')
        if status_param:
            queryset = queryset.filter(status=status_param)
        if category_id:
            include_children = self.request.query_params.get('include_children', 'true')
            try:
                category = Category.objects.get(pk=category_id)
            except Category.DoesNotExist:
                queryset = queryset.none()
            else:
                if include_children in ('1', 'true', 'True'):
                    category_ids = get_category_children_ids(category, active_only=True)
                    queryset = queryset.filter(category_id__in=category_ids)
                else:
                    queryset = queryset.filter(category_id=category_id)
        if keyword:
            queryset = queryset.filter(name__icontains=keyword)
        tenant_id = self.request.query_params.get('tenant_id')
        tenant_code = self.request.query_params.get('tenant_code')
        if self._is_platform_staff() and self.action == 'list':
            all_tenants = self.request.query_params.get('all_tenants', '').lower() in ('1', 'true')
            if not all_tenants and not tenant_id and not tenant_code:
                queryset = queryset.filter(tenant__isnull=True)
        if tenant_id and self._is_platform_staff():
            try:
                queryset = queryset.filter(tenant_id=int(tenant_id))
            except (TypeError, ValueError):
                queryset = queryset.none()
        elif tenant_code and self._is_platform_staff():
            queryset = queryset.filter(tenant__code=tenant_code)

        is_new = self.request.query_params.get('is_new')
        if is_new and str(is_new).lower() in ('true', '1', 'yes'):
            try:
                days = int(self.request.query_params.get('days', 30) or 30)
            except (TypeError, ValueError):
                days = 30
            days = max(1, min(days, 365))
            cutoff = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(created_at__gte=cutoff)
            from django.db.models import IntegerField, OuterRef, Subquery, Sum, Value
            from django.db.models.functions import Coalesce
            from orders.models import Order, OrderItem

            sold_subquery = (
                OrderItem.objects.filter(
                    product_id=OuterRef('pk'),
                    order__status__in=[
                        Order.STATUS_PAID,
                        Order.STATUS_SHIPPED,
                        Order.STATUS_COMPLETED,
                    ],
                )
                .values('product_id')
                .annotate(total=Sum('quantity'))
                .values('total')
            )
            queryset = queryset.annotate(
                sold_count=Coalesce(Subquery(sold_subquery, output_field=IntegerField()), Value(0)),
            ).order_by('-created_at')

        return queryset

    def paginate_queryset(self, queryset):
        page = super().paginate_queryset(queryset)
        if page is not None:
            attach_product_tags(list(page))
        return page

    def list(self, request: Request, *args, **kwargs) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        items = list(queryset)
        attach_product_tags(items)
        serializer = self.get_serializer(items, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        attach_product_tags([instance])
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create product and log initial stock."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            set_inventory_context(changed_by=request.user, remark='商品创建初始库存')
            instance = serializer.save()
        except Exception:
            logger.exception('Create failed')
            return error_response('创建失败', code=50000, http_status=500)
        return success_response(
            data=self.get_serializer(instance).data,
            message='创建成功',
            http_status=status.HTTP_201_CREATED,
        )

    def update(self, request: Request, *args, **kwargs) -> Response:
        """Update product and log stock changes."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            set_inventory_context(changed_by=request.user, remark='商品库存调整')
            instance = serializer.save()
        except Exception:
            logger.exception('Update failed')
            return error_response('更新失败', code=50000, http_status=500)
        return success_response(data=self.get_serializer(instance).data, message='更新成功')

    @action(detail=True, methods=['post'], url_path='on_sale')
    def on_sale(self, request: Request, pk: int | None = None) -> Response:
        """Put product on sale."""
        product = self.get_object()
        try:
            product.status = Product.STATUS_ON_SALE
            product.save(update_fields=['status', 'updated_at'])
        except Exception:
            logger.exception('On sale failed')
            return error_response('上架失败', code=50000, http_status=500)
        return success_response(data=self.get_serializer(product).data, message='商品已上架')

    @action(detail=True, methods=['post'], url_path='off_sale')
    def off_sale(self, request: Request, pk: int | None = None) -> Response:
        """Take product off sale."""
        product = self.get_object()
        try:
            product.status = Product.STATUS_OFF_SALE
            product.save(update_fields=['status', 'updated_at'])
        except Exception:
            logger.exception('Off sale failed')
            return error_response('下架失败', code=50000, http_status=500)
        return success_response(data=self.get_serializer(product).data, message='商品已下架')
