# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Product, ProductAttribute, ProductAttributeRelation, Review, UserBehavior


class ProductAttributeRelationInline(admin.TabularInline):
    model = ProductAttributeRelation
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'brand', 'name_short', 'price', 'sales_volume', 'platform', 'updated_at')
    inlines = [ProductAttributeRelationInline]
    list_filter = ('platform', 'brand')
    search_fields = ('name', 'brand', 'external_id')
    list_per_page = 20

    def name_short(self, obj):
        return obj.name[:40] + '...' if len(obj.name) > 40 else obj.name
    name_short.short_description = '商品名'


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'content_short', 'rating', 'sentiment', 'created_at')
    list_filter = ('sentiment', 'rating')
    search_fields = ('content', 'user_id')
    raw_id_fields = ('product',)

    def content_short(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_short.short_description = '评论'


@admin.register(UserBehavior)
class UserBehaviorAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'product', 'behavior_type', 'quantity', 'price', 'created_at')
    list_filter = ('behavior_type',)
    raw_id_fields = ('product',)
