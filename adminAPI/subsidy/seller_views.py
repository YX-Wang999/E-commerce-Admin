"""Seller subsidy API views."""

from __future__ import annotations

import json

from django.http import HttpResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.media_utils import file_field_url
from common.pagination import StandardPagination
from common.response import error_response, success_response
from products.models import Product
from subsidy.models import SubsidyOrder, SubsidyPolicy, SubsidyProduct
from subsidy.serializers import (
    SellerSubsidyFilingSerializer,
    SubsidyOrderCodesSerializer,
    SubsidyOrderSerializer,
    SubsidyProductSerializer,
)
from subsidy.services import (
    build_filing_export_payload,
    get_active_policy,
    seller_available_products_queryset,
)


class SellerSubsidyProductListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        tenant = request.tenant
        if not tenant:
            return error_response('未绑定店铺', http_status=403)

        filing_status = request.query_params.get('filing_status')
        qs = (
            SubsidyProduct.objects.filter(tenant=tenant)
            .select_related('product', 'policy')
            .order_by('-created_at')
        )
        if filing_status:
            qs = qs.filter(filing_status=filing_status)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        data = SubsidyProductSerializer(page, many=True).data
        return paginator.get_paginated_response(data)

    def post(self, request: Request) -> Response:
        tenant = request.tenant
        if not tenant:
            return error_response('未绑定店铺', http_status=403)

        serializer = SellerSubsidyFilingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product_id = serializer.validated_data['product_id']
        policy_id = serializer.validated_data.get('policy_id')
        region = serializer.validated_data['region']
        category = serializer.validated_data['category']

        product = Product.all_objects.filter(
            id=product_id,
            tenant=tenant,
            is_active=True,
            status=Product.STATUS_ON_SALE,
        ).first()
        if not product:
            return error_response('请选择本店已上架商品')

        existing = SubsidyProduct.objects.filter(product=product).first()
        if existing and existing.filing_status in (
            SubsidyProduct.FILING_SUBMITTED,
            SubsidyProduct.FILING_APPROVED,
        ):
            return error_response('该商品备案进行中或已通过，无法重复提交')

        if policy_id:
            policy = SubsidyPolicy.objects.filter(id=policy_id, is_active=True).first()
        else:
            policy = get_active_policy(region=region, category=category)
        if not policy:
            return error_response('暂无匹配的国补政策')

        now = timezone.now()
        if existing:
            existing.region = region
            existing.category = category
            existing.policy = policy
            existing.filing_status = SubsidyProduct.FILING_SUBMITTED
            existing.filing_submitted_at = now
            existing.filing_reject_reason = ''
            existing.subsidy_amount = 0
            existing.save()
            row = existing
        else:
            row = SubsidyProduct.objects.create(
                product=product,
                tenant=tenant,
                policy=policy,
                region=region,
                category=category,
                filing_status=SubsidyProduct.FILING_SUBMITTED,
                filing_submitted_at=now,
            )

        return success_response(
            SubsidyProductSerializer(row).data,
            message='备案材料已提交，请向当地商务部门完成政府申报',
            http_status=201,
        )


class SellerSubsidyAvailableProductsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        tenant = request.tenant
        if not tenant:
            return error_response('未绑定店铺', http_status=403)

        qs = seller_available_products_queryset(tenant)
        keyword = (request.query_params.get('keyword') or '').strip()
        if keyword:
            qs = qs.filter(name__icontains=keyword)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs.order_by('-updated_at'), request)

        filing_map = {
            row.product_id: row
            for row in SubsidyProduct.objects.filter(tenant=tenant, product_id__in=[p.id for p in page])
        }
        results = []
        for item in page:
            filing = filing_map.get(item.id)
            results.append(
                {
                    'id': item.id,
                    'name': item.name,
                    'price': str(item.price),
                    'image': file_field_url(item.image, item.updated_at),
                    'stock': item.stock,
                    'filing_status': filing.filing_status if filing else 'not_submitted',
                    'filing_status_label': filing.get_filing_status_display() if filing else '未备案',
                },
            )
        return paginator.get_paginated_response(results)


class SellerSubsidyExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, pk: int) -> Response:
        tenant = request.tenant
        if not tenant:
            return error_response('未绑定店铺', http_status=403)
        row = (
            SubsidyProduct.objects.filter(pk=pk, tenant=tenant)
            .select_related('product', 'policy', 'tenant')
            .first()
        )
        if not row:
            return error_response('备案记录不存在', http_status=404)
        return success_response(build_filing_export_payload(row))

    def post(self, request: Request, pk: int) -> HttpResponse:
        tenant = request.tenant
        if not tenant:
            return error_response('未绑定店铺', http_status=403)
        row = (
            SubsidyProduct.objects.filter(pk=pk, tenant=tenant)
            .select_related('product', 'policy', 'tenant')
            .first()
        )
        if not row:
            return error_response('备案记录不存在', http_status=404)
        payload = build_filing_export_payload(row)
        content = json.dumps(payload, ensure_ascii=False, indent=2)
        response = HttpResponse(content, content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="subsidy-filing-{row.id}.json"'
        return response


class SellerSubsidyOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        tenant = request.tenant
        if not tenant:
            return error_response('未绑定店铺', http_status=403)
        qs = (
            SubsidyOrder.objects.filter(tenant=tenant)
            .select_related('order', 'order__customer')
            .prefetch_related('order__items')
            .order_by('-created_at')
        )
        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(SubsidyOrderSerializer(page, many=True).data)


class SellerSubsidyOrderCodesView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request: Request, pk: int) -> Response:
        tenant = request.tenant
        if not tenant:
            return error_response('未绑定店铺', http_status=403)
        row = SubsidyOrder.objects.filter(pk=pk, tenant=tenant).first()
        if not row:
            return error_response('国补订单不存在', http_status=404)
        serializer = SubsidyOrderCodesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        row.sn_code = serializer.validated_data.get('sn_code', '').strip()
        row.imei_code = serializer.validated_data.get('imei_code', '').strip()
        row.save(update_fields=['sn_code', 'imei_code', 'updated_at'])
        return success_response(SubsidyOrderSerializer(row).data, message='SN/IMEI 已保存')
