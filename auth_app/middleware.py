# middleware.py
import logging
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils import timezone

# セキュリティログの設定
security_logger = logging.getLogger('security')

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # ログインページ, adminページ, トップページへのアクセスは除外
        allowed_paths = [reverse('login'), '/admin/', reverse('top')]
        if request.path not in allowed_paths:
            return HttpResponseRedirect(reverse('top'))
        return None


class AdminSecurityMiddleware:
    """管理サイトへの不正アクセスを監視・ブロックするミドルウェア"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # 管理サイトへのアクセス試行をログに記録
        if request.path.startswith('/admin/'):
            self._log_admin_access_attempt(request)
            # ダミーの404ページを返す
            raise Http404("Page not found")
            
        # 一般的な管理パスの試行をブロック
        suspicious_paths = [
            '/administrator/', '/wp-admin/', '/cpanel/', '/phpmyadmin/',
            '/management/', '/control/', '/panel/', '/dashboard/'
        ]
        
        for path in suspicious_paths:
            if request.path.startswith(path):
                self._log_suspicious_access(request, path)
                raise Http404("Page not found")
        
        response = self.get_response(request)
        return response
    
    def _log_admin_access_attempt(self, request):
        """管理サイトアクセス試行をログに記録"""
        security_logger.warning(
            f"Admin access attempt - IP: {self._get_client_ip(request)}, "
            f"Path: {request.path}, User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}, "
            f"Time: {timezone.now()}"
        )
    
    def _log_suspicious_access(self, request, path):
        """不審なアクセスをログに記録"""
        security_logger.critical(
            f"Suspicious access attempt - IP: {self._get_client_ip(request)}, "
            f"Path: {path}, User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}, "
            f"Time: {timezone.now()}"
        )
    
    def _get_client_ip(self, request):
        """クライアントIPアドレスを取得"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
