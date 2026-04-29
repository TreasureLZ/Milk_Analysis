# 维护说明

本项目处于活跃维护阶段，不是 LTS 项目。

当前维护目标是把项目整理成一个适合持续扩展、展示和教学复用的 Django 数据分析案例。

## 当前版本定位

- 可视化优先：核心价值集中在分析 API 与 ECharts 页面。
- 数据可复现：通过 `load_mock_data` 生成商品、评论、属性和用户行为。
- 采集可演示：通过 `crawl_demo_data` 从本地 HTML 页面演示采集、清洗、入库链路。
- 数据可导出：通过 `export_project_data` 导出 SQLite 数据表。
- 适合继续扩展：后续可补真实电商数据、筛选条件、报告导出和部署说明。

## 建议优先维护项

1. 补充首页、市场概览、品牌价格、属性偏好、评论情感、用户分群页面截图。
2. 增加后台商品、评论、用户行为管理截图。
3. 增加 MySQL 配置示例。
4. 补充真实数据字段来源与采集限制说明。
5. 增加 API 文档，方便替换前端或接入其他展示端。
6. 补充情感分析方法说明，区分演示规则和可扩展模型。
7. 增加聚类特征、评估指标和业务解释。

## 不建议立即做的事

- 不建议提交 `.venv/`、`.idea/`、`db.sqlite3`、`exports/` 和 `crawler/raw/`。
- 不建议把演示采集命令伪装成真实线上爬虫。
- 不建议在没有数据来源说明时发布真实平台数据。
- 不建议过早重写前端框架，当前模板页面已经能支撑展示和教学。

## 提交规范建议

```text
docs: update screenshot guide
feat: add product filter
fix: correct price segment aggregation
chore: regenerate readme charts
```

## GitHub Topics 建议

- `django`
- `python`
- `data-analysis`
- `echarts`
- `ecommerce`
- `milk-analysis`
- `dashboard`
- `graduation-project`
