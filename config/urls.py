from django.contrib import admin
from django.urls import path, include
from django.conf import settings

admin.site.site_header = getattr(settings, 'ADMIN_SITE_HEADER', '常温牛奶电商数据挖掘与可视化分析')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('analysis.urls')),
    path('', include('visualization.urls')),
    # 兼容以 /dashboard/ 作为前缀的访问习惯（例如 /dashboard/brand-price/）
    path('dashboard/', include('visualization.urls')),
]
