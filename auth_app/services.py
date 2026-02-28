from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from app.models import Category, PaymentMethod
from .models import LoginHistory

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser
    from django.http import HttpRequest

security_logger = logging.getLogger('security')


def get_client_ip(request: HttpRequest) -> str | None:
    """クライアントのIPアドレスを取得"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def get_location_from_ip(ip_address: str | None) -> str:
    """IPアドレスから地域情報を取得"""
    if not ip_address or ip_address in ['127.0.0.1', 'localhost', '::1']:
        return 'ローカルホスト'

    try:
        response = requests.get(f'https://ipapi.co/{ip_address}/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            city = data.get('city', '')
            region = data.get('region', '')
            country = data.get('country_name', '')
            location_parts = [part for part in [city, region, country] if part]
            return ', '.join(location_parts) if location_parts else '不明'
    except Exception as e:
        security_logger.debug(f'IP地域情報取得エラー: {str(e)}')

    return '不明'


def create_default_user_data(user: AbstractBaseUser) -> None:
    """新規ユーザーのデフォルトデータを作成"""
    PaymentMethod.objects.create(user=user, name='現金')
    Category.objects.create(user=user, name='食費')


def record_login_success(user: AbstractBaseUser, request: HttpRequest) -> None:
    """ログイン成功時の処理（履歴記録・ユーザー情報更新）"""
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    location = get_location_from_ip(ip_address)

    LoginHistory.objects.create(
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
        location=location,
        success=True,
    )

    user.last_login_at = timezone.now()
    user.login_attempt_count += 1
    user.access_count += 1
    user.save(update_fields=['last_login_at', 'login_attempt_count', 'access_count'])


def record_login_failure(email: str | None, request: HttpRequest) -> None:
    """ログイン失敗時の処理（履歴記録・試行回数更新）"""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        user = User.objects.get(email=email)
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        location = get_location_from_ip(ip_address)

        LoginHistory.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            location=location,
            success=False,
        )

        user.login_attempt_count += 1
        user.save(update_fields=['login_attempt_count'])

    except User.DoesNotExist:
        security_logger.warning(f'存在しないユーザーへのログイン試行: {email}')


def notify_admin_login(user: AbstractBaseUser, request: HttpRequest) -> None:
    """管理者・スタッフのログインをログ記録し、メール通知を送信"""
    if not (user.is_superuser or user.is_staff):
        return

    username = user.username
    email = user.email
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    login_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    user_type = []
    if user.is_superuser:
        user_type.append('管理者')
    if user.is_staff:
        user_type.append('スタッフ')
    user_type_str = '・'.join(user_type)

    security_logger.warning(
        f'特権ユーザーログイン検知 | '
        f'ユーザー: {username} ({email}) | '
        f'権限: {user_type_str} | '
        f'IPアドレス: {ip_address} | '
        f'User-Agent: {user_agent} | '
        f'時刻: {login_time}'
    )

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
