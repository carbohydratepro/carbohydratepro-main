from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.core.mail import send_mail
from datetime import datetime
from django.utils import timezone
import logging
import requests

from app.models import PaymentMethod, Category
from .models import LoginHistory

# セキュリティログ用のロガーを設定
security_logger = logging.getLogger('security')

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_default_payment_method_and_category(sender, instance, created, **kwargs):
    if created:
        PaymentMethod.objects.create(user=instance, name="現金")
        Category.objects.create(user=instance, name="食費")


@receiver(user_logged_in)
def record_login_history(sender, request, user, **kwargs):
    """ログイン成功時にログイン履歴を記録"""
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    location = get_location_from_ip(ip_address)
    
    # ログイン履歴を作成
    LoginHistory.objects.create(
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
        location=location,
        success=True
    )
    
    # ユーザー情報を更新
    user.last_login_at = timezone.now()
    user.login_attempt_count += 1
    user.access_count += 1
    user.save(update_fields=['last_login_at', 'login_attempt_count', 'access_count'])


@receiver(user_login_failed)
def record_failed_login(sender, credentials, request, **kwargs):
    """ログイン失敗時にログイン履歴を記録"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # 失敗したログイン試行のユーザーを特定
    email = credentials.get('username')  # USERNAME_FIELDがemailの場合
    try:
        user = User.objects.get(email=email)
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        location = get_location_from_ip(ip_address)
        
        # 失敗履歴を記録
        LoginHistory.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            location=location,
            success=False
        )
        
        # ログイン試行回数を増加
        user.login_attempt_count += 1
        user.save(update_fields=['login_attempt_count'])
        
    except User.DoesNotExist:
        # ユーザーが存在しない場合はログのみ記録
        security_logger.warning(f'存在しないユーザーへのログイン試行: {email}')


@receiver(user_logged_in)
def log_admin_staff_login(sender, request, user, **kwargs):
    """管理者またはスタッフのログインをsecurity.logに記録し、メール通知を送信"""
    
    # 管理者またはスタッフ権限を持つユーザーの場合のみ処理
    if user.is_superuser or user.is_staff:
        # ユーザー情報の取得
        username = user.username
        email = user.email
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        login_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # ユーザーのタイプを判定
        user_type = []
        if user.is_superuser:
            user_type.append('管理者')
        if user.is_staff:
            user_type.append('スタッフ')
        user_type_str = '・'.join(user_type)
        
        # セキュリティログに記録
        security_logger.warning(
            f'特権ユーザーログイン検知 | '
            f'ユーザー: {username} ({email}) | '
            f'権限: {user_type_str} | '
            f'IPアドレス: {ip_address} | '
            f'User-Agent: {user_agent} | '
            f'時刻: {login_time}'
        )
        
        # 即座のメール通知を送信（設定で有効な場合のみ）
        if getattr(settings, 'SEND_INSTANT_SECURITY_EMAIL', False):
            try:
                subject = f'【セキュリティ警告】特権ユーザーログイン検知 - {username}'
                message = f'''
セキュリティ警告: 特権ユーザーのログインが検知されました。

【ログイン情報】
ユーザー名: {username}
メールアドレス: {email}
権限: {user_type_str}
IPアドレス: {ip_address}
ログイン時刻: {login_time}
User-Agent: {user_agent}

このログインが本人によるものでない場合は、直ちにパスワードを変更してください。

---
このメールは即座の通知として自動送信されています。
'''
                
                # セキュリティアラート送信先にメール送信
                recipient_email = getattr(settings, 'SECURITY_ALERT_EMAIL', 'carbohydratepro@gmail.com')
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient_email],
                    fail_silently=False,
                )
                
                security_logger.info(f'即座のセキュリティ警告メールを送信しました: {username} -> {recipient_email}')
                
            except Exception as e:
                security_logger.error(f'メール送信エラー: {str(e)}')


def get_client_ip(request):
    """クライアントのIPアドレスを取得"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_location_from_ip(ip_address):
    """IPアドレスから地域情報を取得"""
    if not ip_address or ip_address in ['127.0.0.1', 'localhost', '::1']:
        return 'ローカルホスト'
    
    try:
        # ipapi.coを使用して地域情報を取得（無料API）
        response = requests.get(f'https://ipapi.co/{ip_address}/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            city = data.get('city', '')
            region = data.get('region', '')
            country = data.get('country_name', '')
            
            # 地域情報を組み合わせ
            location_parts = [part for part in [city, region, country] if part]
            return ', '.join(location_parts) if location_parts else '不明'
    except Exception as e:
        security_logger.debug(f'IP地域情報取得エラー: {str(e)}')
    
    return '不明'
