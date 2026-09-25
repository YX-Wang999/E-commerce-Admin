"""Platform admin tag APIs."""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.response import error_response, success_response
from products.models import Product
from tag_system.models import ProductTagConfig, Tag, TagCategory, TenantTagConfig
from tag_system.product_tag_ops import ProductTagSyncError, sync_product_tags
from tag_system.serializers import (
    ProductTagConfigSerializer,
    TagCategorySerializer,
    TagSerializer,
    TenantTagConfigSerializer,
)


class AdminTagCategoryViewSet(viewsets.ModelViewSet):
    queryset = TagCategory.objects.all().order_by('sort_order', 'id')
    serializer_class = TagCategorySerializer
    permission_classes = [IsAuthenticated]


class AdminTagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.select_related('category').all().order_by('-priority', 'id')
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]


class AdminTenantTagConfigViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TenantTagConfig.objects.select_related('tenant', 'tag').all().order_by('-updated_at')
    serializer_class = TenantTagConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = self.request.query_params.get('tenant')
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        status_value = self.request.query_params.get('status')
        if status_value:
            qs = qs.filter(status=status_value)
        return qs

    @action(detail=True, methods=['post'], url_path='review')
    def review(self, request: Request, pk=None) -> Response:
        row = self.get_object()
        status_value = (request.data.get('status') or '').strip()
        if status_value not in (
            TenantTagConfig.STATUS_APPROVED,
            TenantTagConfig.STATUS_REJECTED,
            TenantTagConfig.STATUS_PENDING,
        ):
            return error_response('无效的审核状态')
        row.status = status_value
        row.reject_reason = (request.data.get('reject_reason') or '').strip()
        if status_value == TenantTagConfig.STATUS_APPROVED:
            row.is_participating = True
        row.save(update_fields=['status', 'reject_reason', 'is_participating', 'updated_at'])
        from approval.models import Approval
        from approval.services import mark_approval_finished

        approval = Approval.objects.filter(
            business_type='tag_system.tenant_config',
            business_id=row.id,
            status=Approval.STATUS_PENDING,
        ).first()
        if approval is not None:
            mark_approval_finished(
                approval,
                status=Approval.STATUS_APPROVED if status_value == TenantTagConfig.STATUS_APPROVED else Approval.STATUS_REJECTED,
                reviewer=request.user,
                reject_reason=row.reject_reason,
                notify_applicant=True,
            )
        return success_response(TenantTagConfigSerializer(row).data, message='审核完成')


class AdminProductTagConfigView(APIView):
    """Platform admin product tag assignment."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        from common.pagination import StandardPagination

        queryset = ProductTagConfig.objects.select_related('product', 'tag').order_by('-updated_at')
        product_id = request.query_params.get('product_id')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
            rows = queryset[: int(request.query_params.get('page_size') or 50)]
            return success_response(
                {
                    'count': queryset.count(),
                    'next': None,
                    'previous': None,
                    'results': ProductTagConfigSerializer(rows, many=True).data,
                },
            )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            return paginator.get_paginated_response(ProductTagConfigSerializer(page, many=True).data)
        return success_response(
            {
                'count': queryset.count(),
                'next': None,
                'previous': None,
                'results': ProductTagConfigSerializer(queryset, many=True).data,
            },
        )

    def post(self, request: Request) -> Response:
        product_id = request.data.get('product_id')
        if not product_id:
            return error_response('请选择商品')
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return error_response('商品不存在')

        active_tag_ids = request.data.get('active_tag_ids')
        if active_tag_ids is not None:
            if not isinstance(active_tag_ids, list):
                return error_response('标签参数格式错误')
            try:
                rows = sync_product_tags(
                    product=product,
                    active_tag_ids=active_tag_ids,
                    source_type=ProductTagConfig.SOURCE_PLATFORM,
                    validate_platform_approval=False,
                )
            except ProductTagSyncError as exc:
                return error_response(str(exc))
            for tag_id in active_tag_ids:
                try:
                    tag = Tag.objects.select_related('category').get(pk=tag_id, is_active=True)
                except Tag.DoesNotExist:
                    continue
                if (
                    product.tenant_id
                    and tag.category.category_type == TagCategory.CATEGORY_PLATFORM
                    and tag.requires_approval
                ):
                    TenantTagConfig.objects.update_or_create(
                        tenant_id=product.tenant_id,
                        tag=tag,
                        defaults={
                            'is_participating': True,
                            'status': TenantTagConfig.STATUS_APPROVED,
                        },
                    )
            return success_response(
                ProductTagConfigSerializer(rows, many=True).data,
                message='商品标签已更新',
            )

        tag_id = request.data.get('tag_id')
        is_active = bool(request.data.get('is_active', True))
        if not tag_id:
            return error_response('请选择标签')
        try:
            tag = Tag.objects.get(pk=tag_id, is_active=True)
        except Tag.DoesNotExist:
            return error_response('标签不存在')

        if is_active:
            active_ids = list(
                ProductTagConfig.objects.filter(product=product, is_active=True)
                .exclude(tag_id=tag.id)
                .values_list('tag_id', flat=True),
            )
            active_ids.append(tag.id)
            try:
                rows = sync_product_tags(
                    product=product,
                    active_tag_ids=active_ids,
                    source_type=ProductTagConfig.SOURCE_PLATFORM,
                    validate_platform_approval=False,
                )
            except ProductTagSyncError as exc:
                return error_response(str(exc))
            row = next((item for item in rows if item.tag_id == tag.id), None)
        else:
            row, _ = ProductTagConfig.objects.update_or_create(
                product=product,
                tag=tag,
                defaults={
                    'is_active': False,
                    'display_text': (request.data.get('display_text') or '').strip(),
                    'source_type': ProductTagConfig.SOURCE_PLATFORM,
                },
            )
            rows = [row]

        if (
            is_active
            and product.tenant_id
            and tag.category.category_type == TagCategory.CATEGORY_PLATFORM
            and tag.requires_approval
        ):
            TenantTagConfig.objects.update_or_create(
                tenant_id=product.tenant_id,
                tag=tag,
                defaults={
                    'is_participating': True,
                    'status': TenantTagConfig.STATUS_APPROVED,
                },
            )
        row = rows[0] if rows else row
        return success_response(ProductTagConfigSerializer(row).data, message='商品标签已更新')
