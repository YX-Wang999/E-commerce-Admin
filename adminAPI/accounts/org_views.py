"""Organization chart API."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.org_chart import get_org_tree
from common.response import success_response


class OrgChartView(APIView):
    """Return role-scoped organization chart."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return nested org chart nodes."""
        nodes = get_org_tree(request.user)
        return success_response(data={'nodes': nodes})
