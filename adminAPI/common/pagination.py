"""Custom pagination with unified response format."""

from rest_framework.pagination import PageNumberPagination

from common.response import success_response


class StandardPagination(PageNumberPagination):
    """Page-number pagination returning unified format."""

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data: list) -> success_response:
        """Return paginated data in unified format."""
        return success_response(
            data={
                'count': self.page.paginator.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'results': data,
            },
        )
