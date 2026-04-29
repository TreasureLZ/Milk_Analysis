# -*- coding: utf-8 -*-
"""
演示型数据采集命令：从本地 HTML 页面“抓取”商品/评论/属性并入库。

目的：
- 让项目具备完整、可复现的“采集 → 清洗/标准化 → 入库 → 分析展示”链路
- 不依赖外网（便于课堂/验收环境运行）

用法：
  python manage.py crawl_demo_data
  python manage.py crawl_demo_data --clear
  python manage.py crawl_demo_data --pages crawler/sources/demo_pages
"""

import json
import os
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import (
    Product,
    ProductAttribute,
    ProductAttributeRelation,
    Review,
)


@dataclass
class ParsedProduct:
    platform: str
    external_id: str
    name: str
    brand: str
    price: Optional[Decimal]
    sales_volume: Optional[int]
    origin: str
    spec: str
    url: str
    raw_attrs: Dict
    tags: List[str]


@dataclass
class ParsedReview:
    product_external_id: str
    user_id: str
    content: str
    rating: Optional[int]
    sentiment: Optional[int]
    like_count: int
    created_at: Optional[timezone.datetime]


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _to_decimal(v: str) -> Optional[Decimal]:
    if v is None:
        return None
    s = str(v).strip().replace("￥", "").replace(",", "")
    if not s:
        return None
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def _to_int(v: str) -> Optional[int]:
    if v is None:
        return None
    s = str(v).strip().replace(",", "")
    if not s:
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def _parse_list_page(html: str, base_dir: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.select("a.product-link[href]"):
        href = a.get("href", "").strip()
        if not href:
            continue
        # list.html 与 detail_xxx.html 同目录
        links.append(os.path.normpath(os.path.join(base_dir, href)))
    return links


def _parse_detail_page(html: str) -> Tuple[ParsedProduct, List[ParsedReview]]:
    soup = BeautifulSoup(html, "html.parser")

    root = soup.select_one("div#product")
    if not root:
        raise ValueError("detail page missing #product root")

    platform = (root.get("data-platform") or "").strip() or "演示平台"
    external_id = (root.get("data-external-id") or "").strip()
    name = (root.select_one("h1.name").get_text(strip=True) if root.select_one("h1.name") else "").strip()
    brand = (root.select_one("span.brand").get_text(strip=True) if root.select_one("span.brand") else "").strip()
    origin = (root.select_one("span.origin").get_text(strip=True) if root.select_one("span.origin") else "").strip()
    spec = (root.select_one("span.spec").get_text(strip=True) if root.select_one("span.spec") else "").strip()

    price = _to_decimal(root.select_one("span.price").get_text(strip=True) if root.select_one("span.price") else "")
    sales_volume = _to_int(root.select_one("span.sales").get_text(strip=True) if root.select_one("span.sales") else "")

    url = (root.get("data-url") or "").strip()

    tags = [x.get_text(strip=True) for x in soup.select("ul.tags li.tag")]
    raw_attrs = {}
    raw_json = soup.select_one("script#raw-json")
    if raw_json and raw_json.get_text(strip=True):
        try:
            raw_attrs = json.loads(raw_json.get_text())
        except Exception:
            raw_attrs = {"raw_json_error": True, "text": raw_json.get_text()[:2000]}

    product = ParsedProduct(
        platform=platform,
        external_id=external_id,
        name=name,
        brand=brand,
        price=price,
        sales_volume=sales_volume,
        origin=origin,
        spec=spec,
        url=url,
        raw_attrs=raw_attrs,
        tags=tags,
    )

    reviews: List[ParsedReview] = []
    for div in soup.select("div.review"):
        user_id = (div.get("data-user") or "").strip() or "anonymous"
        rating = _to_int(div.get("data-rating"))
        sentiment = _to_int(div.get("data-sentiment"))
        like_count = _to_int(div.get("data-likes")) or 0
        created_at = None
        created_raw = (div.get("data-created-at") or "").strip()
        if created_raw:
            # 允许 YYYY-MM-DD
            try:
                created_at = timezone.make_aware(timezone.datetime.fromisoformat(created_raw))
            except Exception:
                created_at = None
        content = div.get_text(" ", strip=True)
        if content:
            reviews.append(
                ParsedReview(
                    product_external_id=external_id,
                    user_id=user_id,
                    content=content,
                    rating=rating,
                    sentiment=sentiment,
                    like_count=like_count,
                    created_at=created_at,
                )
            )

    return product, reviews


class Command(BaseCommand):
    help = "演示型采集：从本地 HTML 抓取商品/评论并入库"

    def add_arguments(self, parser):
        parser.add_argument("--pages", type=str, default="crawler/sources/demo_pages", help="演示页面目录（相对项目根）")
        parser.add_argument("--clear", action="store_true", help="采集前清空商品/评论/属性数据")
        parser.add_argument("--raw-out", type=str, default="crawler/raw/demo", help="原始数据落盘目录（相对项目根）")

    @transaction.atomic
    def handle(self, *args, **options):
        pages_dir = options["pages"]
        raw_out = options["raw_out"]
        clear = bool(options.get("clear"))

        if not os.path.isabs(pages_dir):
            pages_dir = os.path.join(os.getcwd(), pages_dir)
        if not os.path.isabs(raw_out):
            raw_out = os.path.join(os.getcwd(), raw_out)

        os.makedirs(raw_out, exist_ok=True)

        if clear:
            self.stdout.write("清空现有数据（Product/Review/Attribute）...")
            Review.objects.all().delete()
            ProductAttributeRelation.objects.all().delete()
            Product.objects.all().delete()
            ProductAttribute.objects.all().delete()

        list_path = os.path.join(pages_dir, "list.html")
        if not os.path.exists(list_path):
            raise FileNotFoundError(f"未找到演示列表页：{list_path}")

        list_html = _read_text(list_path)
        detail_paths = _parse_list_page(list_html, pages_dir)
        if not detail_paths:
            self.stdout.write(self.style.WARNING("列表页未解析到商品链接，未采集到数据。"))
            return

        # 采集（解析）阶段：输出原始结构化 JSON，便于展示“采集过程”
        parsed_products: List[ParsedProduct] = []
        parsed_reviews: List[ParsedReview] = []
        for p in detail_paths:
            detail_html = _read_text(p)
            product, reviews = _parse_detail_page(detail_html)
            parsed_products.append(product)
            parsed_reviews.extend(reviews)

        with open(os.path.join(raw_out, "products_raw.json"), "w", encoding="utf-8") as f:
            json.dump([p.__dict__ for p in parsed_products], f, ensure_ascii=False, indent=2, default=str)
        with open(os.path.join(raw_out, "reviews_raw.json"), "w", encoding="utf-8") as f:
            json.dump([r.__dict__ for r in parsed_reviews], f, ensure_ascii=False, indent=2, default=str)

        # 清洗/标准化与入库：对 Product 做 upsert，对属性做词表与关系表
        products_created = 0
        products_updated = 0
        reviews_created = 0
        attrs_created = 0
        rel_created = 0

        extid_to_product: Dict[str, Product] = {}
        for p in parsed_products:
            if not p.external_id or not p.name:
                continue
            obj, created = Product.objects.update_or_create(
                external_id=p.external_id,
                defaults={
                    "platform": p.platform,
                    "name": p.name,
                    "brand": p.brand,
                    "price": p.price,
                    "sales_volume": p.sales_volume,
                    "sales_amount": (p.price * p.sales_volume) if (p.price is not None and p.sales_volume is not None) else None,
                    "origin": p.origin,
                    "spec": p.spec,
                    "url": p.url,
                    "raw_attrs": p.raw_attrs or {},
                },
            )
            extid_to_product[p.external_id] = obj
            products_created += 1 if created else 0
            products_updated += 0 if created else 1

            for tag in p.tags:
                if not tag:
                    continue
                a, a_created = ProductAttribute.objects.get_or_create(name=tag, defaults={"description": tag})
                if a_created:
                    attrs_created += 1
                _, r_created = ProductAttributeRelation.objects.get_or_create(product=obj, attribute=a)
                if r_created:
                    rel_created += 1

        for r in parsed_reviews:
            product = extid_to_product.get(r.product_external_id)
            if not product or not r.content:
                continue
            Review.objects.create(
                product=product,
                user_id=r.user_id or "",
                content=r.content,
                rating=r.rating,
                sentiment=r.sentiment,
                like_count=r.like_count or 0,
                created_at=r.created_at,
            )
            reviews_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                "采集完成：商品 新增%d/更新%d，评论 新增%d，属性 新增%d，属性关系 新增%d。原始数据已输出到：%s"
                % (products_created, products_updated, reviews_created, attrs_created, rel_created, raw_out)
            )
        )

