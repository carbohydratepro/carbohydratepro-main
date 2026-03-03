from collections.abc import Callable
from django.http import Http404, HttpRequest, HttpResponse
from django.conf import settings
from django.urls import resolve
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)


class MaintenanceModeMiddleware:
    """
    メンテナンスモード中はメンテナンスページを表示するミドルウェア。
    スタッフユーザーはメンテナンスページをバイパスできる。
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if getattr(settings, 'MAINTENANCE_MODE', False):
            # スタッフユーザーはメンテナンスページをスキップ
            if request.user.is_authenticated and request.user.is_staff:
                return self.get_response(request)
            # 静的ファイルとメンテナンスページ自体はスルー
            if request.path.startswith('/static/') or request.path.startswith('/media/'):
                return self.get_response(request)
            return render(request, 'maintenance.html', status=503)

        return self.get_response(request)

class AdminSecurityMiddleware:
    """
    管理サイトへのアクセスを制限するミドルウェア
    """
    
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # 管理サイトが無効になっている場合は404を返す
        if not getattr(settings, 'ADMIN_ENABLED', True):
            try:
                resolved = resolve(request.path_info)
                if 'admin' in resolved.namespace or 'admin' in resolved.url_name:
                    logger.warning(f"Blocked admin access attempt from {request.META.get('REMOTE_ADDR', 'unknown')} to {request.path}")
                    raise Http404("Page not found")
            except (Http404, ValueError, AttributeError):
                # resolve に失敗した場合は通常通り処理を続行
                pass
        
        # 管理サイトへのアクセス試行をログに記録
        if '/admin' in request.path or 'system-control-panel' in request.path:
            user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
            ip_address = request.META.get('REMOTE_ADDR', 'unknown')
            
            if request.user.is_authenticated:
                logger.info(f"Admin access by user {request.user.username} from {ip_address}")
            else:
                logger.warning(f"Unauthenticated admin access attempt from {ip_address} - User-Agent: {user_agent}")
        
        response = self.get_response(request)
        return response