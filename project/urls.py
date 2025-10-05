"""project URL Configuration

The `urlpatterns` list routes urlpatterns = [
    # 推測困難な管理URL（本番環境では更に複雑にすることを推奨）
    path('system-control-panel-x7k9m2/', secure_admin_site.urls),
    # 元の管理URLは404エラーを返す
    path('admin/', lambda request: Http404()),
    # SEO対策
    path('robots.txt', robots_txt),
    path('carbohydratepro/', include('app.urls')),
    path('', include('auth_app.urls')),
]views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
import os

# 管理サイトのカスタマイズ
class SecureAdminSite(AdminSite):
    site_header = 'システム管理'
    site_title = 'システム管理'
    index_title = 'システム管理'
    
    def has_permission(self, request):
        # スーパーユーザーかつスタッフのみアクセス可能
        return request.user.is_active and request.user.is_superuser and request.user.is_staff

# カスタム管理サイトのインスタンス作成
secure_admin_site = SecureAdminSite(name='secure_admin')

# 既存の登録済みモデルを新しい管理サイトに移行
from django.apps import apps
for app_config in apps.get_app_configs():
    for model in app_config.get_models():
        if admin.site.is_registered(model):
            model_admin = admin.site._registry[model]
            secure_admin_site.register(model, model_admin.__class__)

# robots.txt配信用のビュー
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /",  # すべてのパスをdisallow
        "",
        "# すべてのページのインデックス化を防ぐ",
        "# 検索エンジンによるクロールを完全に拒否",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

urlpatterns = [
    # 推測困難な管理URL（本番環境では更に複雑にすること推奨）
    path('system-control-panel-x7k9m2/', secure_admin_site.urls),
    # 元の管理URLは404エラーを返す
    path('admin/', lambda request: Http404()),
    path('carbohydratepro/', include('app.urls')),
    path('', include('auth_app.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)