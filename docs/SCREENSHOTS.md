# 截图补充建议

当前 README 已放入基于演示数据库生成的统计 SVG 图表。后续建议继续补充真实页面截图。

## 推荐截图清单

| 文件名 | 建议页面 | 说明 |
| --- | --- | --- |
| `dashboard.png` | `/` | 展示项目入口和模块导航 |
| `market-overview.png` | `/market/` | 展示品牌集中度、价格段、平台占比 |
| `brand-price.png` | `/brand-price/` | 展示品牌销量和价格段竞争格局 |
| `attribute-preference.png` | `/attribute/` | 展示属性频次和属性共现 |
| `review-sentiment.png` | `/review/` | 展示评论情感、评分和主题关注 |
| `user-clusters.png` | `/user/` | 展示用户分群画像 |
| `admin-products.png` | `/admin/core/product/` | 展示商品数据管理 |
| `admin-reviews.png` | `/admin/core/review/` | 展示评论数据管理 |

建议统一放到：

```text
docs/images/
```

README 中可按以下方式引用：

```md
![市场概览](docs/images/market-overview.png)
```

## 截图前准备

建议先执行：

```bash
python manage.py migrate
python manage.py load_mock_data --clear
python scripts/generate_readme_charts.py
python manage.py runserver
```

然后打开：

```text
http://127.0.0.1:8000/
```
