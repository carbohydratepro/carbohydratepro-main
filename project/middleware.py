from django.http import Http404
from django.conf import settings
from django.urls import resolve
import logging

logger = logging.getLogger(__name__)

class AdminSecurityMiddleware:
    """
    管理サイトへのアクセスを制限するミドルウェア
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 管理サイトが無効になっている場合は404を返す
        if not getattr(settings, 'ADMIN_ENABLED', True):
            try:
                resolved = resolve(request.path_info)
                if 'admin' in resolved.namespace or 'admin' in resolved.url_name:
                    logger.warning(f"Blocked admin access attempt from {request.META.get('REMOTE_ADDR', 'unknown')} to {request.path}")
                    raise Http404("Page not found")
            except:
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