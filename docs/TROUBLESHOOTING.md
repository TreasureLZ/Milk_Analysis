# 常见问题

## 页面可以打开，但图表为空

先确认数据库里是否有演示数据：

```bash
python manage.py shell -c "from core.models import Product, Review, UserBehavior; print(Product.objects.count(), Review.objects.count(), UserBehavior.objects.count())"
```

如果数量为 0，执行：

```bash
python manage.py load_mock_data --clear
```

## 接口返回 500

先运行 Django 检查：

```bash
python manage.py check
```

再确认迁移已执行：

```bash
python manage.py migrate
```

## 用户分群页面没有结果

用户分群依赖 `UserBehavior` 数据，至少需要 3 个用户样本。建议重新生成演示数据：

```bash
python manage.py load_mock_data --clear --users 800
```

## README 图表没有更新

README 中的 SVG 图表是静态文件。数据库变化后需要重新生成：

```bash
python scripts/generate_readme_charts.py
```

## ECharts 资源加载失败

项目已将 ECharts 放到本地静态资源：

```text
visualization/static/visualization/vendor/echarts.min.js
```

如果部署到生产环境，执行：

```bash
python manage.py collectstatic
```

## 后台无法登录

如果没有管理员账号，执行：

```bash
python manage.py createsuperuser
```

然后访问：

```text
http://127.0.0.1:8000/admin/
```
