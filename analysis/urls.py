# -*- coding: utf-8 -*-
"""数据分析 API 接口"""
from django.urls import path
from . import views

urlpatterns = [
    path('market/overview/', views.market_overview),
    path('market/brand-price/', views.brand_price_analysis),
    path('attribute/preference/', views.attribute_preference),
    path('review/sentiment/', views.review_sentiment),
    path('user/clusters/', views.user_clusters),
]
