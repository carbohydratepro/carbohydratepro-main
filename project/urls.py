"""project URL Configuration

The `urlpatterns` list routes urlpatterns = [
    # 推測困難な管理URL（本番環境では更に複雑にすることを推奨）
    path('system-control-panel/', secure_admin_site.urls),
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
from django.http import Http404, HttpRequest, HttpResponse
from django.contrib.admin.sites import AdminSite
from django.contrib.sitemaps.views import sitemap
from auth_app.sitemaps import PublicPagesSitemap
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
def robots_txt(request: HttpRequest) -> HttpResponse:
    site_url = f"{settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}"
    lines = [
        "User-agent: *",
        "# 認証が必要なページ・管理画面はクロール禁止",
        "Disallow: /carbohydratepro/",
        "Disallow: /system-control-panel/",
        "Disallow: /admin/",
        "Disallow: /password_reset/",
        "Disallow: /password_change/",
        "Disallow: /edit/",
        "Disallow: /verify-email/",
        "",
        f"Sitemap: {site_url}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

sitemaps = {
    'static': PublicPagesSitemap,
}

urlpatterns = [
    # 推測困難な管理URL（本番環境では更に複雑にすること推奨）
    path('system-control-panel/', secure_admin_site.urls),
    # 元の管理URLは404エラーを返す
    path('admin/', lambda request: Http404()),
    # SEO
    path('robots.txt', robots_txt),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('carbohydratepro/', include('app.urls')),
    path('', include('auth_app.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)