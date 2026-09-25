"""Report URL routes."""

from django.urls import path

from reports.views import (
    CustomerAnalysisView,
    DashboardSummaryView,
    FinanceSummaryView,
    ProductRankView,
    PromotionAnalysisView,
    SalesReportView,
)

urlpatterns = [
    path('dashboard/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('sales/', SalesReportView.as_view(), name='sales-report'),
    path('product-rank/', ProductRankView.as_view(), name='product-rank'),
    path('customer/', CustomerAnalysisView.as_view(), name='customer-analysis'),
    path('promotion/', PromotionAnalysisView.as_view(), name='promotion-analysis'),
    path('finance/', FinanceSummaryView.as_view(), name='finance-summary'),
]
