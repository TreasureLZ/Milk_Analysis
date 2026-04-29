# -*- coding: utf-8 -*-
"""Generate lightweight SVG charts for README previews from the local database."""

from __future__ import annotations

import html
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402
from django.db.models import Count, Sum  # noqa: E402


django.setup()

from core.models import Product, ProductAttributeRelation, Review  # noqa: E402


OUT_DIR = ROOT / "docs" / "images"
COLORS = ["#0ea5e9", "#10b981", "#8b5cf6", "#f59e0b", "#ec4899", "#6366f1", "#14b8a6", "#f97316"]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def compact_number(value: float) -> str:
    value = float(value or 0)
    if abs(value) >= 100000000:
        return f"{value / 100000000:.2f}亿"
    if abs(value) >= 10000:
        return f"{value / 10000:.1f}万"
    return f"{value:.0f}"


def svg_shell(title: str, body: str, width: int = 760, height: int = 420) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">
  <rect width="100%" height="100%" fill="#ffffff"/>
  <text x="28" y="42" font-family="Noto Sans SC, Microsoft YaHei, Arial, sans-serif" font-size="22" font-weight="700" fill="#0f172a">{esc(title)}</text>
  {body}
</svg>
"""


def bar_chart(title: str, rows: list[tuple[str, float]], path: Path, value_suffix: str = "") -> None:
    width, height = 760, 420
    left, top, bar_h, gap = 160, 78, 24, 16
    max_value = max([v for _, v in rows] or [1])
    chart_w = width - left - 132
    parts = []
    if not rows:
        parts.append('<text x="28" y="100" font-size="16" fill="#64748b">暂无数据</text>')
    for i, (label, value) in enumerate(rows):
        y = top + i * (bar_h + gap)
        bar_w = 0 if max_value == 0 else int(chart_w * (float(value) / max_value))
        color = COLORS[i % len(COLORS)]
        parts.append(f'<text x="28" y="{y + 18}" font-family="Noto Sans SC, Microsoft YaHei, Arial, sans-serif" font-size="14" fill="#334155">{esc(label)}</text>')
        parts.append(f'<rect x="{left}" y="{y}" width="{chart_w}" height="{bar_h}" rx="6" fill="#e2e8f0"/>')
        parts.append(f'<rect x="{left}" y="{y}" width="{bar_w}" height="{bar_h}" rx="6" fill="{color}"/>')
        parts.append(f'<text x="{left + chart_w + 16}" y="{y + 18}" font-family="Arial, sans-serif" font-size="14" fill="#0f172a">{esc(compact_number(value) + value_suffix)}</text>')
    path.write_text(svg_shell(title, "\n  ".join(parts), width, height), encoding="utf-8")


def sentiment_chart(path: Path) -> None:
    mapping = {-1: "负面", 0: "中性", 1: "正面"}
    rows = Review.objects.values("sentiment").annotate(count=Count("id")).order_by("sentiment")
    data = [(mapping.get(row["sentiment"], "未标注"), int(row["count"] or 0)) for row in rows]
    total = sum(v for _, v in data) or 1
    parts = []
    x0, y0, w, h, gap = 80, 105, 560, 42, 24
    for i, (label, value) in enumerate(data):
        y = y0 + i * (h + gap)
        pct = value / total
        color = COLORS[[2, 5, 1][i] if i < 3 else i % len(COLORS)]
        parts.append(f'<text x="80" y="{y - 12}" font-family="Noto Sans SC, Microsoft YaHei, Arial, sans-serif" font-size="15" fill="#334155">{esc(label)}：{value:,} 条（{pct:.1%}）</text>')
        parts.append(f'<rect x="{x0}" y="{y}" width="{w}" height="{h}" rx="9" fill="#e2e8f0"/>')
        parts.append(f'<rect x="{x0}" y="{y}" width="{int(w * pct)}" height="{h}" rx="9" fill="{color}"/>')
    path.write_text(svg_shell("评论情感分布", "\n  ".join(parts), 760, 360), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    brand_rows = [
        (row["brand"] or "未知", float(row["sales"] or 0))
        for row in Product.objects.values("brand").annotate(sales=Sum("sales_amount")).order_by("-sales")[:8]
    ]
    bar_chart("品牌销售额 Top8", brand_rows, OUT_DIR / "brand-sales-top8.svg")

    bins = [(0, 50), (50, 100), (100, 150), (150, 200), (200, 300), (300, 10000)]
    price_rows = []
    for low, high in bins:
        label = f"{low}-{high}元" if high < 10000 else f"{low}元+"
        price_rows.append((label, Product.objects.filter(price__gte=low, price__lt=high).count()))
    bar_chart("价格段商品分布", price_rows, OUT_DIR / "price-segment-distribution.svg", " 件")

    sentiment_chart(OUT_DIR / "sentiment-distribution.svg")

    attr_rows = [
        (row["attribute__name"] or "未分类", int(row["count"] or 0))
        for row in ProductAttributeRelation.objects.values("attribute__name").annotate(count=Count("product")).order_by("-count")
    ]
    bar_chart("产品属性偏好", attr_rows, OUT_DIR / "attribute-preference.svg", " 件")

    print(f"Generated README charts in {OUT_DIR}")


if __name__ == "__main__":
    main()
