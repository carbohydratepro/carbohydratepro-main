from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.core.mail import send_mail
from datetime import datetime
import logging

from app.models import PaymentMethod, Category

# セキュリティログ用のロガーを設定
security_logger = logging.getLogger('security')

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_default_payment_method_and_category(sender, instance, created, **kwargs):
    if created:
        PaymentMethod.objects.create(user=instance, name="現金")
        Category.objects.create(user=instance, name="食費")


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
