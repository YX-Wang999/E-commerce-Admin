"""Customer mall subsidy API views."""

from __future__ import annotations

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.media_utils import file_field_url
from common.pagination import StandardPagination
from common.response import error_response, success_response
from products.models import Product
from subsidy.models import SubsidyProduct
from subsidy.services import (
    build_subsidy_payload,
    calculate_for_product,
    check_subsidy_eligibility,
    get_active_policy,
)


class CustomerSubsidyProductListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        qs = (
            SubsidyProduct.objects.filter(
                filing_status=SubsidyProduct.FILING_APPROVED,
                policy__is_active=True,
                product__is_active=True,
                product__status=Product.STATUS_ON_SALE,
            )
            .select_related('product', 'tenant', 'policy')
            .order_by('-filing_submitted_at', '-id')
        )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        results = []
        for row in page:
            payload = build_subsidy_payload(
                product=row.product,
                policy=row.policy,
                subsidy_amount=row.subsidy_amount,
            )
            results.append(
                {
                    'id': row.id,
                    'product_id': row.product_id,
                    'name': row.product.name,
                    'image': file_field_url(row.product.image, row.product.updated_at),
                    'price': payload['original_price'],
                    'region': row.region,
                    'category': row.category,
                    'tenant_name': row.tenant.name if row.tenant_id else '',
                    **payload,
                },
            )
        return paginator.get_paginated_response(results)


class CustomerSubsidyCalculateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        product_id = request.query_params.get('product_id')
        if not product_id:
            return error_response('缺少 product_id')
        try:
            quantity = int(request.query_params.get('quantity') or 1)
        except (TypeError, ValueError):
            quantity = 1

        data = calculate_for_product(int(product_id), quantity)
        if not data:
            return success_response({'is_subsidy': False})

        policy = get_active_policy()
        return success_response(
            {
                **data,
                'policy_description': data.get('policy_description') or (policy.description if policy else ''),
            },
        )


class CustomerSubsidyEligibilityView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        product_id = request.query_params.get('product_id')
        if not product_id:
            return error_response('缺少 product_id')
        region = (request.query_params.get('region') or '').strip()
        customer = getattr(request, 'customer', None)
        return success_response(
            check_subsidy_eligibility(
                product_id=int(product_id),
                customer=customer,
                region=region,
            ),
        )
