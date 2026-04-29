# 常温牛奶电商数据挖掘与可视化分析 — 项目说明

技术栈：Django + django-simpleui + ECharts + Python 数据科学库（Pandas、Scikit-learn 等）。

---

## 一、系统目标

构建涵盖**数据采集、存储、分析挖掘与可视化展示**的完整数据分析系统：

1. 对电商平台常温牛奶数据的**多维度挖掘**
2. 揭示**消费升级趋势**与品牌、价格段格局
3. 精准分析**不同用户群体的偏好差异**（K-Means 分群）
4. 形成可复现的分析流程与可视化报告

---

## 二、接口与页面

| 类型 | 路径 | 说明 |
|------|------|------|
| 页面 | `/` | 仪表盘入口 |
| 页面 | `/market/` | 市场总体态势概览 |
| 页面 | `/brand-price/` | 品牌与价格段竞争格局分析 |
| 页面 | `/attribute/` | 产品功能属性偏好解读 |
| 页面 | `/review/` | 评论情感洞察 |
| 页面 | `/user/` | 用户分群 / 用户画像 |
| API | `/api/market/overview/` | 市场概览数据 |
| API | `/api/market/brand-price/` | 品牌与价格段数据 |
| API | `/api/attribute/preference/` | 属性偏好与关联规则 |
| API | `/api/review/sentiment/` | 评论情感与主题 |
| API | `/api/user/clusters/` | 用户分群数据 |

---

## 三、系统架构

| 模块         | 功能                     | 实现方式                    |
|--------------|--------------------------|-----------------------------|
| 数据管理     | 商品、评论、用户行为 CRUD | 后台 Admin（django-simpleui） |
| 数据采集     | 爬虫、数据导入           | 管理命令，结果写入 DB       |
| 消费特征分析 | 统计、关联规则、聚类、情感分析 | analysis 应用，返回 JSON   |
| 可视化展示   | 图表与仪表盘             | 前端 ECharts + 模板页       |

项目代码位于 **milk_analysis/**：

```
milk_analysis/
├── config/           # 项目配置
├── core/             # 核心数据模型（商品、评论、用户行为、产品属性）
├── crawler/          # 数据采集（import_sample_data、load_mock_data）
├── analysis/         # 数据分析 API
├── visualization/    # 可视化页面
├── templates/        # 基模板与各分析页
└── requirements.txt, manage.py, README.md
```

---

## 四、数据模型

- **Product**：常温牛奶商品（平台、品牌、价格、销量、销售额、规格等）
- **ProductAttribute / ProductAttributeRelation**：功能属性标签（有机、高钙、A2β-酪蛋白等）及与商品的多对多关系
- **Review**：用户评论（内容、评分、情感极性）
- **UserBehavior**：用户行为/购买记录（用于分群与画像）

---

## 五、实现要点

- **市场格局**：描述性统计、品牌集中度 CRn、价格段与平台分布
- **属性偏好**：属性商品数、属性共现（同一商品多属性）
- **评论情感**：情感极性分布、评分分布、主题占位
- **用户分群**：K-Means 聚类（消费金额、订单数、品牌数等特征），群体画像与雷达图
- **可视化**：ECharts 柱状图、饼图、玫瑰图、折线图、雷达图等，统一配色与响应式

---

## 六、运行环境

- Python 3.12
- SQLite（默认），无需 MySQL
- 可选：Jupyter 用于离线分析与报告导出

按“数据管理 → 分析 → 可视化”链路使用即可。
