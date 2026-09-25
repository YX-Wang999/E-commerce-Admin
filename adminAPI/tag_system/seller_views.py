"""Seller tag APIs."""

import logging

from django.db import DatabaseError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination
from common.response import error_response, success_response
from products.models import Product
from tag_system.models import ProductTagConfig, Tag, TagCategory, TenantTagConfig
from tag_system.product_tag_ops import ProductTagSyncError, _is_missing_table_error, sync_product_tags
from tag_system.serializers import ProductTagConfigSerializer, TagSerializer, TenantTagConfigSerializer
from tenants.seller_permissions import IsTenantStaffMember, get_request_tenant

logger = logging.getLogger(__name__)


def _parse_bool(value, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


def _resolve_tenant(request: Request):
    tenant = get_request_tenant(request)
    if tenant is None:
        return None, error_response('未找到商家信息', http_status=403)
    return tenant, None


def _get_seller_product(tenant, product_id):
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return None
    return Product.all_objects.filter(tenant=tenant, pk=product_id).first()


class SellerTagListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        tenant, err = _resolve_tenant(request)
        if err:
            return err
        try:
            tags = Tag.objects.filter(is_active=True, can_tenant_use=True).select_related('category').order_by('-priority')
            tenant_configs = {
                cfg.tag_id: cfg
                for cfg in TenantTagConfig.objects.filter(tenant=tenant).select_related('tag')
            }
            data = []
            for tag in tags:
                item = TagSerializer(tag).data
                cfg = tenant_configs.get(tag.id)
                item['participating'] = bool(
                    cfg and cfg.is_participating and cfg.status == TenantTagConfig.STATUS_APPROVED,
                )
                item['config_status'] = cfg.status if cfg else ''
                item['config_id'] = cfg.id if cfg else None
                data.append(item)
            return success_response(data=data)
        except DatabaseError as exc:
            logger.exception('Seller tag list failed')
            if _is_missing_table_error(exc):
                return error_response('标签功能未初始化，请执行 migrate tag_system', code=50001, http_status=500)
            return error_response('标签数据读取失败，请稍后重试', code=50002, http_status=500)


class SellerTagConfigView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def post(self, request: Request) -> Response:
        tenant, err = _resolve_tenant(request)
        if err:
            return err
        tag_id = request.data.get('tag_id')
        participating = _parse_bool(request.data.get('is_participating'), default=False)
        if not tag_id:
            return error_response('请选择标签')
        try:
            tag = Tag.objects.get(pk=tag_id, is_active=True)
        except Tag.DoesNotExist:
            return error_response('标签不存在')

        defaults = {
            'is_participating': participating,
            'custom_name': (request.data.get('custom_name') or '').strip(),
        }
        if tag.requires_approval and participating:
            defaults['status'] = TenantTagConfig.STATUS_PENDING
        elif participating:
            defaults['status'] = TenantTagConfig.STATUS_APPROVED
        else:
            defaults['status'] = TenantTagConfig.STATUS_APPROVED
            defaults['is_participating'] = False

        row, _ = TenantTagConfig.objects.update_or_create(
            tenant=tenant,
            tag=tag,
            defaults=defaults,
        )
        message = '已提交参与申请，等待平台审核' if row.status == TenantTagConfig.STATUS_PENDING else '标签配置已更新'
        if row.status == TenantTagConfig.STATUS_PENDING:
            from approval.services import sync_tag_approval

            sync_tag_approval(row)
        return success_response(TenantTagConfigSerializer(row).data, message=message)


class SellerProductTagConfigListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]

    def get(self, request: Request) -> Response:
        tenant, err = _resolve_tenant(request)
        if err:
            return err
        try:
            queryset = ProductTagConfig.objects.filter(
                product__tenant=tenant,
            ).select_related('product', 'tag').order_by('-updated_at')
            product_id = request.query_params.get('product_id')
            if product_id:
                queryset = queryset.filter(product_id=product_id)
                try:
                    limit = int(request.query_params.get('page_size') or 100)
                except (TypeError, ValueError):
                    limit = 100
                rows = queryset[:limit]
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
        except DatabaseError as exc:
            logger.exception('Seller product tag list failed')
            if _is_missing_table_error(exc):
                return error_response('标签功能未初始化，请执行 migrate tag_system', code=50001, http_status=500)
            return error_response('标签数据读取失败，请稍后重试', code=50002, http_status=500)

    def post(self, request: Request) -> Response:
        tenant, err = _resolve_tenant(request)
        if err:
            return err

        product_id = request.data.get('product_id')
        if not product_id:
            return error_response('请选择商品')

        product = _get_seller_product(tenant, product_id)
        if product is None:
            return error_response('商品不存在')

        active_tag_ids = request.data.get('active_tag_ids')
        if active_tag_ids is not None:
            if not isinstance(active_tag_ids, list):
                return error_response('标签参数格式错误')
            try:
                rows = sync_product_tags(
                    product=product,
                    active_tag_ids=active_tag_ids,
                    source_type=ProductTagConfig.SOURCE_TENANT,
                    validate_platform_approval=True,
                )
            except ProductTagSyncError as exc:
                return error_response(str(exc))
            except DatabaseError as exc:
                logger.exception('Seller product tag batch save failed')
                if _is_missing_table_error(exc):
                    return error_response('标签功能未初始化，请执行 migrate tag_system', code=50001, http_status=500)
                return error_response('标签保存失败，请稍后重试', code=50002, http_status=500)
            return success_response(
                ProductTagConfigSerializer(rows, many=True).data,
                message='商品标签已更新',
            )

        tag_id = request.data.get('tag_id')
        is_active = _parse_bool(request.data.get('is_active'), default=True)
        if not tag_id:
            return error_response('请选择标签')

        try:
            tag = Tag.objects.select_related('category').get(pk=tag_id, is_active=True)
        except Tag.DoesNotExist:
            return error_response('标签不存在')
        except DatabaseError as exc:
            logger.exception('Seller product tag lookup failed')
            if _is_missing_table_error(exc):
                return error_response('标签功能未初始化，请执行 migrate tag_system', code=50001, http_status=500)
            return error_response('标签数据读取失败，请稍后重试', code=50002, http_status=500)

        category = getattr(tag, 'category', None)
        if (
            is_active
            and category
            and category.category_type == TagCategory.CATEGORY_PLATFORM
            and tag.requires_approval
        ):
            cfg = TenantTagConfig.objects.filter(
                tenant=tenant,
                tag=tag,
                is_participating=True,
                status=TenantTagConfig.STATUS_APPROVED,
            ).first()
            if not cfg:
                return error_response('请先申请并等待平台审核通过该标签活动')

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
                    source_type=ProductTagConfig.SOURCE_TENANT,
                    validate_platform_approval=True,
                )
            except ProductTagSyncError as exc:
                return error_response(str(exc))
            except DatabaseError as exc:
                logger.exception('Seller product tag save failed')
                if _is_missing_table_error(exc):
                    return error_response('标签功能未初始化，请执行 migrate tag_system', code=50001, http_status=500)
                return error_response('标签保存失败，请稍后重试', code=50002, http_status=500)
            row = next((item for item in rows if item.tag_id == tag.id), None)
            if row is None:
                row, _ = ProductTagConfig.objects.update_or_create(
                    product=product,
                    tag=tag,
                    defaults={
                        'is_active': True,
                        'display_text': (request.data.get('display_text') or '').strip(),
                        'source_type': ProductTagConfig.SOURCE_TENANT,
                    },
                )
            return success_response(ProductTagConfigSerializer(row).data, message='商品标签已更新')

        try:
            row, _ = ProductTagConfig.objects.update_or_create(
                product=product,
                tag=tag,
                defaults={
                    'is_active': False,
                    'display_text': (request.data.get('display_text') or '').strip(),
                    'source_type': ProductTagConfig.SOURCE_TENANT,
                },
            )
        except DatabaseError as exc:
            logger.exception('Seller product tag save failed')
            if _is_missing_table_error(exc):
                return error_response('标签功能未初始化，请执行 migrate tag_system', code=50001, http_status=500)
            return error_response('标签保存失败，请稍后重试', code=50002, http_status=500)

        return success_response(ProductTagConfigSerializer(row).data, message='商品标签已更新')
