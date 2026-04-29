# -*- coding: utf-8 -*-
"""
数据分析 API 视图：市场概览、品牌价格、属性偏好、评论情感、用户分群。
基于 core 模型聚合，返回供 ECharts 使用的 JSON。
"""
from decimal import Decimal
from django.db.models import Sum, Count, Avg
from django.http import JsonResponse

from core.models import Product, Review, UserBehavior, ProductAttribute, ProductAttributeRelation


def _decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _decimal_to_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decimal_to_float(x) for x in obj]
    return obj


def market_overview(request):
    """
    市场总体态势：总销售额、总销量、品牌集中度 CRn、价格段分布
    """
    products = Product.objects.all()
    total_sales = products.aggregate(s=Sum('sales_amount'))['s'] or 0
    total_volume = products.aggregate(s=Sum('sales_volume'))['s'] or 0

    brand_sales = list(
        products.values('brand')
        .annotate(sales=Sum('sales_amount'), volume=Sum('sales_volume'))
        .order_by('-sales')
    )
    total_sales_float = float(total_sales) if total_sales else 0
    crn = []
    cum = 0
    for i, b in enumerate(brand_sales[:10]):
        s = float(b['sales'] or 0)
        cum += s
        crn.append({
            'rank': i + 1,
            'brand': b['brand'] or '未知',
            'sales': s,
            'volume': b['volume'] or 0,
            'share': round(cum / total_sales_float * 100, 1) if total_sales_float else 0,
        })

    prices = list(products.exclude(price__isnull=True).values_list('price', flat=True))
    bins = [(0, 50), (50, 100), (100, 150), (150, 200), (200, 300), (300, 10000)]
    price_distribution = []
    for low, high in bins:
        label = f'{low}-{high}元' if high < 10000 else f'{low}元+'
        cnt = sum(1 for p in prices if low <= float(p) < high)
        price_distribution.append({'segment': label, 'count': cnt})

    platform_dist = list(
        products.values('platform')
        .annotate(sales=Sum('sales_amount'), volume=Sum('sales_volume'), count=Count('id'))
    )
    platform_distribution = [
        {'name': x['platform'] or '其他', 'sales': float(x['sales'] or 0), 'volume': x['volume'] or 0, 'count': x['count']}
        for x in platform_dist
    ]

    return JsonResponse({
        'module': 'market_overview',
        'data': _decimal_to_float({
            'total_sales': total_sales,
            'total_volume': total_volume,
            'product_count': products.count(),
            'crn': crn,
            'price_distribution': price_distribution,
            'platform_distribution': platform_distribution,
        }),
        'status': 'ok',
    })


def brand_price_analysis(request):
    """
    品牌与价格段：品牌销量/销售额排名、价格段分布（按商品数）
    """
    products = Product.objects.all()
    brand_ranking = list(
        products.values('brand')
        .annotate(sales=Sum('sales_amount'), volume=Sum('sales_volume'), count=Count('id'))
        .order_by('-volume')[:15]
    )
    price_segments = []
    for low, high in [(0, 30), (30, 60), (60, 100), (100, 150), (150, 300), (300, 10000)]:
        label = f'{low}-{high}元' if high < 10000 else f'{low}元+'
        cnt = products.filter(price__gte=low, price__lt=high).count()
        price_segments.append({'segment': label, 'count': cnt})

    return JsonResponse({
        'module': 'brand_price',
        'data': _decimal_to_float({
            'brand_ranking': [dict(x) for x in brand_ranking],
            'price_segments': price_segments,
        }),
        'status': 'ok',
    })


def attribute_preference(request):
    """
    产品功能属性：各属性商品数、简单共现（同一商品拥有的属性对）
    """
    attr_freq = list(
        ProductAttributeRelation.objects.values('attribute__name')
        .annotate(count=Count('product'))
        .order_by('-count')
    )
    attribute_freq = [{'name': x['attribute__name'] or '未分类', 'value': x['count']} for x in attr_freq]

    product_ids_with_attrs = set(
        ProductAttributeRelation.objects.values_list('product_id', flat=True).distinct()
    )
    from collections import defaultdict
    pair_count = defaultdict(int)
    for pid in list(product_ids_with_attrs)[:500]:
        attrs = list(
            ProductAttributeRelation.objects.filter(product_id=pid)
            .values_list('attribute__name', flat=True)
        )
        attrs = [a for a in attrs if a]
        for i in range(len(attrs)):
            for j in range(i + 1, len(attrs)):
                a, b = attrs[i], attrs[j]
                if a > b:
                    a, b = b, a
                pair_count[(a, b)] += 1
    association_rules = [
        {'items': [k[0], k[1]], 'count': v}
        for k, v in sorted(pair_count.items(), key=lambda x: -x[1])[:20]
    ]

    return JsonResponse({
        'module': 'attribute_preference',
        'data': {
            'attribute_freq': attribute_freq,
            'association_rules': association_rules,
        },
        'status': 'ok',
    })


def review_sentiment(request):
    """
    评论情感：情感极性分布、评分分布、主题关注（基于关键词的轻量规则统计）
    """
    reviews = Review.objects.all()
    sentiment_dist = list(
        reviews.values('sentiment')
        .annotate(count=Count('id'))
    )
    sentiment_map = {-1: '负面', 0: '中性', 1: '正面'}
    sentiment_dist = [
        {'name': sentiment_map.get(s['sentiment'], '未标注'), 'value': s['count']}
        for s in sentiment_dist
    ]
    if not sentiment_dist:
        sentiment_dist = [{'name': '正面', 'value': 0}, {'name': '中性', 'value': 0}, {'name': '负面', 'value': 0}]

    rating_dist = list(
        reviews.exclude(rating__isnull=True)
        .values('rating')
        .annotate(count=Count('id'))
        .order_by('rating')
    )
    rating_dist = [{'rating': r['rating'], 'count': r['count']} for r in rating_dist]

    # 主题关注：关键词规则（避免“占位符”，也便于论文解释与复现）
    topic_rules = {
        '口感风味': ['口感', '味道', '奶香', '香', '醇', '腥'],
        '营养健康': ['营养', '健康', '高钙', '蛋白', '配料', '有机', '低脂', '全脂', '脱脂', 'A2'],
        '包装便利': ['包装', '便携', '携带', '开盖', '密封', '纸盒', '破损'],
        '物流时效': ['物流', '配送', '快递', '到货', '发货', '速度', '慢', '快'],
    }
    topics_count = {k: 0 for k in topic_rules.keys()}
    total = reviews.count()
    # 为性能考虑：抽样最多 20000 条进行主题统计（对展示足够稳定）
    for txt in reviews.values_list('content', flat=True)[:20000]:
        if not txt:
            continue
        for topic, keys in topic_rules.items():
            if any(k in txt for k in keys):
                topics_count[topic] += 1

    topics = [{'name': k, 'value': int(v)} for k, v in topics_count.items()]

    return JsonResponse({
        'module': 'review_sentiment',
        'data': {
            'sentiment_dist': sentiment_dist,
            'rating_dist': rating_dist,
            'topics': topics,
            'total_reviews': total,
        },
        'status': 'ok',
    })


def user_clusters(request):
    """
    用户分群：按用户聚合消费金额/次数，简单分档或 K-Means 聚类
    """
    from collections import defaultdict
    user_stats = defaultdict(lambda: {'total_amount': 0, 'count': 0, 'brands': set()})
    for ub in UserBehavior.objects.select_related('product').all()[:20000]:
        uid = ub.user_id
        user_stats[uid]['count'] += ub.quantity or 1
        if ub.price is not None:
            user_stats[uid]['total_amount'] += float(ub.price) * (ub.quantity or 1)
        if ub.product_id and ub.product:
            user_stats[uid]['brands'].add(ub.product.brand or '')

    rows = []
    for uid, s in user_stats.items():
        rows.append({
            'user_id': uid,
            'total_amount': s['total_amount'],
            'count': s['count'],
            'brand_count': len(s['brands']),
        })

    if len(rows) < 3:
        return JsonResponse({
            'module': 'user_clusters',
            'data': {'clusters': [], 'cluster_profiles': [], 'user_count': len(rows)},
            'status': 'ok',
        })

    try:
        import os
        import warnings
        os.environ.setdefault('LOKY_MAX_CPU_COUNT', '1')
        warnings.filterwarnings(
            'ignore',
            message='.*physical cores.*',
            category=UserWarning,
            module='joblib.externals.loky.backend.context',
        )
        from sklearn.cluster import KMeans
        import numpy as np
        X = [[r['total_amount'], r['count'], r['brand_count']] for r in rows]
        X = np.array(X)
        n = min(4, len(rows) - 1)
        km = KMeans(n_clusters=n, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        for i, r in enumerate(rows):
            r['cluster'] = int(labels[i])
        cluster_profiles = []
        for c in range(n):
            sub = [r for r in rows if r['cluster'] == c]
            cluster_profiles.append({
                'cluster': c,
                'label': ['高端品质型', '实用性价比型', '新潮尝鲜型', '多样探索型'][c] if c < 4 else f'群体{c+1}',
                'count': len(sub),
                'avg_amount': sum(r['total_amount'] for r in sub) / len(sub),
                'avg_count': sum(r['count'] for r in sub) / len(sub),
            })
        clusters = rows
    except Exception:
        clusters = rows
        cluster_profiles = []

    return JsonResponse({
        'module': 'user_clusters',
        'data': _decimal_to_float({
            'clusters': clusters[:100],
            'cluster_profiles': cluster_profiles,
            'user_count': len(rows),
        }),
        'status': 'ok',
    })
