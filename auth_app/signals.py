from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from . import services


@receiver(user_logged_in)
def record_login_history(sender, request, user, **kwargs):
    """ログイン成功時にログイン履歴を記録"""
    services.record_login_success(user, request)


@receiver(user_login_failed)
def record_failed_login(sender, credentials, request, **kwargs):
    """ログイン失敗時にログイン履歴を記録"""
    email = credentials.get('username')
    services.record_login_failure(email, request)


@receiver(user_logged_in)
def log_admin_staff_login(sender, request, user, **kwargs):
    """管理者またはスタッフのログインをログ記録・メール通知"""
    services.notify_admin_login(user, request)
