"""Approval URL routes."""

from django.urls import path

from approval.admin_views import (
    ApprovalApproveView,
    ApprovalBatchApproveView,
    ApprovalDetailView,
    ApprovalListView,
    ApprovalRejectView,
    ApprovalSummaryView,
)

urlpatterns = [
    path('admin/approvals/summary/', ApprovalSummaryView.as_view(), name='approval-summary'),
    path('admin/approvals/', ApprovalListView.as_view(), name='approval-list'),
    path('admin/approvals/<int:pk>/', ApprovalDetailView.as_view(), name='approval-detail'),
    path('admin/approvals/<int:pk>/approve/', ApprovalApproveView.as_view(), name='approval-approve'),
    path('admin/approvals/<int:pk>/reject/', ApprovalRejectView.as_view(), name='approval-reject'),
    path('admin/approvals/batch-approve/', ApprovalBatchApproveView.as_view(), name='approval-batch-approve'),
]
