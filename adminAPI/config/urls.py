"""Project URL configuration."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from customers.auth_views import SendSmsView
from reports.views import DashboardTodosView

urlpatterns = [
    re_path(
        r'^media/(?P<path>.*)$',
        serve,
        {'document_root': settings.MEDIA_ROOT},
        name='serve-media',
    ),
    path('admin/', admin.site.urls),
    path('api/send-sms/', SendSmsView.as_view(), name='send-sms-alias'),
    path('api/', include('accounts.urls')),
    path('api/', include('rbac.urls')),
    path('api/audit/', include('audit.urls')),
    path('api/system/', include('system.urls')),
    path('api/products/', include('products.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/admin/orders/', include('orders.admin_urls')),
    path('api/logistics/', include('logistics.urls')),
    path('api/customers/', include('customers.urls')),
    path('api/feedback/', include('feedback.urls')),
    path('api/announcements/', include('announcement.urls')),
    path('api/points/', include('points.urls')),
    path('api/points-mall/', include('points_mall.urls')),
    path('api/admin/points-mall/', include('points_mall.admin_urls')),
    path('api/customer/seller-points/', include('seller_points.urls')),
    path('api/admin/seller-points/', include('seller_points.admin_urls')),
    path('api/coupons/', include('promotion.mall_urls')),
    path('api/seckill/', include('promotion.seckill_urls')),
    path('api/super-discount/', include('promotion.super_discount_urls')),
    path('api/groupbuy/', include('promotion.groupbuy_urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/dashboard/todos/', DashboardTodosView.as_view(), name='dashboard-todos'),
    path('api/promotions/', include('promotion.urls')),
    path('api/', include('cart.urls')),
    path('api/', include('addresses.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/complaints/', include('complaints.urls')),
    path('api/', include('tenants.urls')),
    path('api/', include('tenants.seller_urls')),
    path('api/', include('notification.urls')),
    path('api/upload/', include('common.urls')),
    path('api/admin/subsidy/', include('subsidy.admin_urls')),
    path('api/customer/subsidy/', include('subsidy.customer_urls')),
    path('api/membership/', include('membership.customer_urls')),
    path('api/admin/membership/', include('membership.admin_urls')),
    path('api/admin/tags/', include('tag_system.admin_urls')),
    path('api/admin/reviews/', include('reviews.admin_urls')),
    path('api/', include('shop_closure.urls')),
    path('api/', include('shop_rating.urls')),
    path('api/', include('approval.urls')),
]

# 兼容旧写法；主路由已在 urlpatterns 顶部注册 serve-media
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
