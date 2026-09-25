"""Complaint stats for admin dashboard."""

from django.db.models import Count
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import Complaint
from common.response import success_response
from complaints.permissions import IsPlatformComplaintStaff


class ComplaintStatsView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformComplaintStaff]

    def get(self, request: Request) -> Response:
        pending = Complaint.objects.filter(status=Complaint.STATUS_PLATFORM_REVIEWING).count()
        by_category = list(
            Complaint.objects.filter(status=Complaint.STATUS_PLATFORM_REVIEWING)
            .values('category')
            .annotate(count=Count('id'))
            .order_by('-count'),
        )
        return success_response(
            data={
                'pending_count': pending,
                'by_category': by_category,
            },
        )
