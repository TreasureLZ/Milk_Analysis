# -*- coding: utf-8 -*-
"""
核心数据模型：商品（常温牛奶）、产品属性、评论、用户行为
"""
from django.db import models


class Product(models.Model):
    """常温牛奶商品"""
    platform = models.CharField('平台', max_length=32, blank=True)
    external_id = models.CharField('平台商品ID', max_length=64, blank=True, db_index=True)
    name = models.CharField('商品名称', max_length=512)
    brand = models.CharField('品牌', max_length=128, blank=True, db_index=True)
    price = models.DecimalField('价格', max_digits=10, decimal_places=2, null=True, blank=True)
    sales_volume = models.IntegerField('销量', null=True, blank=True)
    sales_amount = models.DecimalField('销售额', max_digits=14, decimal_places=2, null=True, blank=True)
    origin = models.CharField('产地', max_length=128, blank=True)
    spec = models.CharField('规格', max_length=128, blank=True)
    url = models.URLField('链接', max_length=1024, blank=True)
    raw_attrs = models.JSONField('原始属性/标签', default=dict, blank=True)
    created_at = models.DateTimeField('入库时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '商品（常温牛奶）'
        verbose_name_plural = verbose_name
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.brand or '未知'} - {self.name[:50]}"


class ProductAttribute(models.Model):
    """产品功能属性标签（有机、高钙、A2β-酪蛋白、进口奶源等）"""
    name = models.CharField('属性名', max_length=64, unique=True)
    description = models.CharField('说明', max_length=256, blank=True)

    class Meta:
        verbose_name = '产品属性标签'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class ProductAttributeRelation(models.Model):
    """商品与属性多对多"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attribute_relations')
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name='products')

    class Meta:
        verbose_name = '商品-属性关联'
        unique_together = [('product', 'attribute')]


class Review(models.Model):
    """用户评论"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user_id = models.CharField('用户标识', max_length=64, blank=True, db_index=True)
    content = models.TextField('评论内容')
    rating = models.SmallIntegerField('评分', null=True, blank=True)
    sentiment = models.SmallIntegerField('情感极性', null=True, blank=True)
    like_count = models.IntegerField('点赞数', default=0)
    created_at = models.DateTimeField('评论时间', null=True, blank=True)
    crawled_at = models.DateTimeField('抓取时间', auto_now_add=True)

    class Meta:
        verbose_name = '评论'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product_id} - {self.content[:30]}..."


class UserBehavior(models.Model):
    """用户行为/购买记录"""
    user_id = models.CharField('用户标识', max_length=64, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='behaviors')
    behavior_type = models.CharField('行为类型', max_length=32, default='purchase')
    quantity = models.IntegerField('数量', default=1)
    price = models.DecimalField('成交价', max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField('行为时间', auto_now_add=True)

    class Meta:
        verbose_name = '用户行为'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user_id} - {self.product_id} - {self.behavior_type}"
