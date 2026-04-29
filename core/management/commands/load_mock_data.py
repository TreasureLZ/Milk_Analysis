# -*- coding: utf-8 -*-
"""
加载模拟数据：商品、属性、评论、用户行为。
用法：
  python manage.py load_mock_data [--clear]
  python manage.py load_mock_data --clear --products 1200 --users 800 --seed 42
"""
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from core.models import Product, ProductAttribute, ProductAttributeRelation, Review, UserBehavior


BRANDS = [
    '蒙牛', '伊利', '光明', '君乐宝', '三元', '认养一头牛', '德亚', '安佳', '德运', '欧德堡',
    '纽仕兰', '圣牧', '完达山', '新希望', '现代牧业', '西域春', '天润', '麦趣尔',
]
ORIGINS = ['内蒙古', '河北', '上海', '北京', '新西兰', '德国', '澳大利亚', '新疆', '黑龙江']
SPECS = ['250ml*24盒', '250ml*16盒', '200ml*24盒', '1L*12盒', '250ml*12盒', '200ml*16盒', '250ml*20盒', '1L*6盒']
ATTR_NAMES = ['有机', '高钙', 'A2β-酪蛋白', '进口奶源', '低脂', '儿童', '全脂', '脱脂']
PLATFORMS = ['京东', '天猫']

REVIEW_SAMPLES = [
    ('口感很好，奶味浓', 5, 1), ('营养健康，孩子爱喝', 5, 1), ('包装完好，物流快', 4, 1),
    ('一般般，性价比还行', 3, 0), ('有点腥味', 2, -1), ('品质不错，会回购', 5, 1),
    ('包装方便携带', 4, 1), ('物流慢了点', 3, -1), ('很新鲜，日期新', 5, 1),
    ('价格实惠', 4, 1), ('味道一般', 3, 0), ('推荐购买', 5, 1), ('分量足', 4, 1),
    ('口感醇厚', 5, 1), ('适合早餐', 4, 1), ('包装破损', 2, -1), ('性价比高', 5, 1),
]


def random_date(days_back=90):
    return timezone.now() - timedelta(days=random.randint(0, days_back))


class Command(BaseCommand):
    help = '加载常温牛奶模拟数据（商品、属性、评论、用户行为）'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='先清空再导入')
        parser.add_argument('--products', type=int, default=1200, help='商品数量（默认 1200）')
        parser.add_argument('--users', type=int, default=800, help='用户数量（默认 800）')
        parser.add_argument('--seed', type=int, default=42, help='随机种子（默认 42，可复现）')

    def handle(self, *args, **options):
        seed = options.get('seed', 42)
        random.seed(seed)

        if options.get('clear'):
            self.stdout.write('清空现有数据...')
            UserBehavior.objects.all().delete()
            Review.objects.all().delete()
            ProductAttributeRelation.objects.all().delete()
            Product.objects.all().delete()
            ProductAttribute.objects.all().delete()

        attrs = []
        for name in ATTR_NAMES:
            a, _ = ProductAttribute.objects.get_or_create(name=name, defaults={'description': name})
            attrs.append(a)

        product_n = max(1, int(options.get('products') or 1200))
        user_n = max(3, int(options.get('users') or 800))

        # 商品：默认 1200 条（更接近展示与聚合统计需要的数据规模）
        # 口径控制：为了论文展示与仪表盘可读性，将“总销售额”控制在约 100~200 万量级
        products_to_create = []
        product_attr_relations = []
        for i in range(product_n):
            brand = random.choice(BRANDS)
            price = Decimal(str(round(random.uniform(22, 220), 2)))
            # 控制销量量级（小量级 + 轻微头部/长尾）
            r = random.random()
            if r < 0.08:
                vol = random.randint(20, 60)      # 爆品
            elif r < 0.43:
                vol = random.randint(6, 20)       # 中尾
            else:
                vol = random.randint(1, 6)        # 长尾
            amt = price * vol
            products_to_create.append(
                Product(
                    platform=random.choice(PLATFORMS),
                    external_id=f'mock_{i+2000}',
                    name=f'{brand} 纯牛奶 常温 {random.choice(SPECS)}',
                    brand=brand,
                    price=price,
                    sales_volume=vol,
                    sales_amount=amt,
                    origin=random.choice(ORIGINS),
                    spec=random.choice(SPECS),
                )
            )

        products = Product.objects.bulk_create(products_to_create, batch_size=1000)

        # 属性关系批量生成（ignore_conflicts 兼容重复约束）
        for p in products:
            n_attr = random.randint(1, 5) if random.random() > 0.08 else random.randint(0, 2)
            if n_attr and attrs:
                chosen = random.sample(attrs, min(n_attr, len(attrs)))
                for a in chosen:
                    product_attr_relations.append(ProductAttributeRelation(product=p, attribute=a))
        if product_attr_relations:
            ProductAttributeRelation.objects.bulk_create(product_attr_relations, batch_size=2000, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(f'创建商品 {len(products)} 条'))

        # 评论：默认更大规模，保证情感/评分分布稳定（总量约 2~6 万）
        reviews_to_create = []
        for p in products:
            r = random.random()
            if r < 0.12:
                n_reviews = random.randint(60, 180)
            elif r < 0.67:
                n_reviews = random.randint(18, 60)
            else:
                n_reviews = random.randint(6, 18)
            for _ in range(n_reviews):
                content, rating, sentiment = random.choice(REVIEW_SAMPLES)
                reviews_to_create.append(
                    Review(
                        product=p,
                        user_id=f'u_{random.randint(1000, 19999)}',
                        content=content,
                        rating=rating,
                        sentiment=sentiment,
                        like_count=random.randint(0, 50),
                        created_at=random_date(90),
                    )
                )
        Review.objects.bulk_create(reviews_to_create, batch_size=5000)
        self.stdout.write(self.style.SUCCESS(f'创建评论 {len(reviews_to_create)} 条'))

        # 用户行为：默认 800 用户，每人 10~45 条（约 1~3 万），用于分群稳定展示
        user_ids = [f'user_{i}' for i in range(1, user_n + 1)]
        behaviors_to_create = []
        for uid in user_ids:
            for _ in range(random.randint(10, 45)):
                p = random.choice(products)
                price = p.price or Decimal('50')
                qty = random.randint(1, 4)
                behaviors_to_create.append(
                    UserBehavior(
                        user_id=uid,
                        product=p,
                        behavior_type='purchase',
                        quantity=qty,
                        price=price,
                        created_at=random_date(120),
                    )
                )
        UserBehavior.objects.bulk_create(behaviors_to_create, batch_size=5000)
        self.stdout.write(self.style.SUCCESS(f'创建用户行为 {len(behaviors_to_create)} 条'))
        self.stdout.write(self.style.SUCCESS('模拟数据加载完成。刷新前端即可查看。'))
