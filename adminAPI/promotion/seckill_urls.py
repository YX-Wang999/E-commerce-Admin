"""Seckill mall URLs."""

from django.urls import path

from promotion.mall_views import SeckillActivitiesView, SeckillBuyView, SeckillProductsView

urlpatterns = [
    path('activities/', SeckillActivitiesView.as_view(), name='seckill-activities'),
    path('products/', SeckillProductsView.as_view(), name='seckill-products'),
    path('<int:pk>/buy/', SeckillBuyView.as_view(), name='seckill-buy'),
]
