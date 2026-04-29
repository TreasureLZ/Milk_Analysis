# -*- coding: utf-8 -*-
from django.shortcuts import render


def index(request):
    return render(request, 'visualization/index.html')


def market_overview_page(request):
    return render(request, 'visualization/market_overview.html')


def brand_price_page(request):
    return render(request, 'visualization/brand_price.html')


def attribute_page(request):
    return render(request, 'visualization/attribute.html')


def review_page(request):
    return render(request, 'visualization/review.html')


def user_clusters_page(request):
    return render(request, 'visualization/user_clusters.html')
