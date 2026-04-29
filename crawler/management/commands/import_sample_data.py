# -*- coding: utf-8 -*-
"""
管理命令占位：从 CSV/JSON 导入样本数据到 core 模型。
爬虫采集并清洗后，可由此命令导入 DB。
用法：python manage.py import_sample_data [--file path/to/data.csv]
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '导入常温牛奶样本数据（CSV/JSON）到 Product、Review 等，后续可扩展'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='数据文件路径（可选）')

    def handle(self, *args, **options):
        file_path = options.get('file')
        if not file_path:
            self.stdout.write(self.style.WARNING('未指定 --file，当前为占位。请准备清洗后的 CSV/JSON 后传入。'))
            return
        # TODO: 使用 pandas 读取 file_path，解析后创建 core.models.Product / Review / UserBehavior
        self.stdout.write(self.style.SUCCESS('导入逻辑待实现，文件: %s' % file_path))
