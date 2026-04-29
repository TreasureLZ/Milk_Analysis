# -*- coding: utf-8 -*-
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('market/', views.market_overview_page),
    path('brand-price/', views.brand_price_page),
    path('attribute/', views.attribute_page),
    path('review/', views.review_page),
    path('user/', views.user_clusters_page),
]
