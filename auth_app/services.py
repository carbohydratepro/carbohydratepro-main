from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import close_old_connections, transaction
from django.db.models import Q
from django.utils import timezone

from app.models import Category, PaymentMethod
from .models import AccountGroup, AccountGroupLink, AccountMembership, LoginHistory

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser
    from django.http import HttpRequest

security_logger = logging.getLogger('security')

ACCOUNT_GROUP_SESSION_KEY = 'account_group_id'
ACCOUNT_ACTIVE_USER_IDS_SESSION_KEY = 'account_active_user_ids'

LOCAL_IP_ADDRESSES = frozenset({'127.0.0.1', 'localhost', '::1'})


def get_client_ip(request: HttpRequest) -> str | None:
    """クライアントのIPアドレスを取得

    X-Forwarded-For はクライアントが任意の値を先頭に付加できるため、
    信頼できるリバースプロキシ（Nginx）が最後に付加した右端の値を使う。
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[-1].strip()
    return request.META.get('REMOTE_ADDR')


def get_location_from_ip(ip_address: str | None) -> str:
    """IPアドレスから地域情報を取得"""
    if not ip_address or ip_address in LOCAL_IP_ADDRESSES:
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


def _update_login_history_location(history_pk: int, ip_address: str | None) -> None:
    """バックグラウンドスレッドからログイン履歴の地域情報を更新する。"""
    try:
        location = get_location_from_ip(ip_address)
        LoginHistory.objects.filter(pk=history_pk).update(location=location)
    except Exception as e:
        security_logger.debug(f'ログイン履歴の地域情報更新エラー: {str(e)}')
    finally:
        close_old_connections()


def schedule_location_resolution(history: LoginHistory) -> None:
    """地域情報の解決をログイン処理をブロックせずに行う。

    外部API（ipapi.co）への問い合わせが必要な場合のみバックグラウンドで実行する。
    """
    ip_address = history.ip_address
    if not ip_address or ip_address in LOCAL_IP_ADDRESSES:
        history.location = get_location_from_ip(ip_address)
        history.save(update_fields=['location'])
        return

    thread = threading.Thread(
        target=_update_login_history_location,
        args=(history.pk, ip_address),
        daemon=True,
    )
    thread.start()


def is_login_locked(email: str | None) -> bool:
    """直近のログイン失敗が上限に達し、一時ロック中のアカウントかを判定する。

    直近 LOGIN_LOCKOUT_WINDOW_MINUTES 分間で、最後の成功より後の失敗が
    LOGIN_LOCKOUT_THRESHOLD 回以上あればロックとみなす。
    ロック中は認証処理自体を行わないため失敗履歴は増えず、
    最後の失敗から時間経過すれば自動的に解除される。
    """
    if not email:
        return False

    User = get_user_model()
    user = User.objects.filter(email=email).first()
    if user is None:
        return False

    threshold = getattr(settings, 'LOGIN_LOCKOUT_THRESHOLD', 5)
    window_minutes = getattr(settings, 'LOGIN_LOCKOUT_WINDOW_MINUTES', 15)
    window_start = timezone.now() - timedelta(minutes=window_minutes)

    recent_histories = user.login_histories.filter(login_time__gte=window_start)
    last_success_time = (
        recent_histories.filter(success=True)
        .order_by('-login_time')
        .values_list('login_time', flat=True)
        .first()
    )
    failures = recent_histories.filter(success=False)
    if last_success_time is not None:
        failures = failures.filter(login_time__gt=last_success_time)

    if failures.count() >= threshold:
        security_logger.warning(f'ロック中アカウントへのログイン試行: {email}')
        return True
    return False


def create_default_user_data(user: AbstractBaseUser) -> None:
    """新規ユーザーのデフォルトデータを作成"""
    PaymentMethod.objects.create(user=user, name='現金')
    Category.objects.create(user=user, name='食費')


def ensure_account_group(user: AbstractBaseUser, created_by: AbstractBaseUser | None = None) -> AccountGroup:
    """ユーザーのアカウントグループを取得し、なければ作成する。"""
    try:
        return user.account_membership.group
    except AccountMembership.DoesNotExist:
        group = AccountGroup.objects.create()
        AccountMembership.objects.create(group=group, user=user, created_by=created_by)
        return group


def get_related_group_ids(group: AccountGroup) -> set[int]:
    """切替候補となるグループIDを返す。

    「ファミリー」= 親グループ + その直接の子グループ。
    自分が親のファミリー（自分＋直接の子）と、自分が子として属する
    ファミリー（親＋その兄弟）を合わせた範囲を返す。
    孫（子の子）や、子・兄弟の別の親は辿らない。
    """
    related_ids = {group.pk}

    # 自分が親のファミリー: 直接の子グループ
    related_ids.update(
        AccountGroupLink.objects.filter(parent=group).values_list('child_id', flat=True)
    )

    # 自分が子として属するファミリー: 親グループとその子（兄弟）グループ
    parent_ids = set(
        AccountGroupLink.objects.filter(child=group).values_list('parent_id', flat=True)
    )
    related_ids.update(parent_ids)
    if parent_ids:
        related_ids.update(
            AccountGroupLink.objects.filter(parent_id__in=parent_ids).values_list('child_id', flat=True)
        )

    return related_ids


def get_related_memberships(group: AccountGroup) -> list[AccountMembership]:
    """グループから切替可能な全アカウント所属を返す（認証済み・有効のみ）。"""
    return list(
        AccountMembership.objects
        .filter(
            group_id__in=get_related_group_ids(group),
            user__is_active=True,
            user__is_email_verified=True,
        )
        .select_related('user')
        .order_by('created_at')
    )


@transaction.atomic
def link_accounts(
    source_user: AbstractBaseUser,
    target_user: AbstractBaseUser,
    created_by: AbstractBaseUser | None = None,
) -> AccountGroup:
    """対象ユーザーのグループを現在ユーザーのグループの子として連携する。

    グループの合流は行わないため、対象が既に持っている他の連携
    （対象の子や別の親）が現在ユーザー側へ波及することはない。
    """
    source_group = ensure_account_group(source_user, created_by=created_by)
    target_group = ensure_account_group(target_user, created_by=created_by or source_user)

    if target_group.pk == source_group.pk:
        return source_group

    # 逆方向（対象が親）の関係が既にあれば、二重の親子関係は作らない
    if AccountGroupLink.objects.filter(parent=target_group, child=source_group).exists():
        return source_group

    AccountGroupLink.objects.get_or_create(
        parent=source_group,
        child=target_group,
        defaults={'created_by': created_by or source_user},
    )
    return source_group


def remember_account_group(request: HttpRequest, group: AccountGroup) -> None:
    """現在のセッションにアカウントグループを記録する。"""
    request.session[ACCOUNT_GROUP_SESSION_KEY] = group.pk


def activate_group_accounts(request: HttpRequest, group: AccountGroup) -> None:
    """セッション内でログイン済みとして切替可能なアカウント一覧を更新する。"""
    active_user_ids = [membership.user_id for membership in get_related_memberships(group)]
    request.session[ACCOUNT_ACTIVE_USER_IDS_SESSION_KEY] = active_user_ids


def remember_authenticated_account(request: HttpRequest, user: AbstractBaseUser) -> AccountGroup:
    """ログイン済みユーザーのグループと有効アカウントをセッションへ保存する。"""
    group = ensure_account_group(user)
    remember_account_group(request, group)
    active_user_ids = request.session.get(ACCOUNT_ACTIVE_USER_IDS_SESSION_KEY)
    if active_user_ids is not None:
        normalized_user_ids = {int(user_id) for user_id in active_user_ids}
        normalized_user_ids.add(user.pk)
        verified_user_ids = {
            membership.user_id for membership in get_related_memberships(group)
        }
        request.session[ACCOUNT_ACTIVE_USER_IDS_SESSION_KEY] = [
            user_id for user_id in normalized_user_ids if user_id in verified_user_ids
        ]
    else:
        activate_group_accounts(request, group)
    return group


def restore_account_session(
    request: HttpRequest,
    group: AccountGroup,
    active_user_ids: list[int],
    authenticated_user: AbstractBaseUser | None = None,
) -> None:
    """Djangoログイン後にアカウント切替用セッション情報を復元する。"""
    remember_account_group(request, group)
    normalized_user_ids = {int(user_id) for user_id in active_user_ids}
    if authenticated_user is not None:
        normalized_user_ids.add(authenticated_user.pk)

    verified_user_ids = [
        membership.user_id for membership in get_related_memberships(group)
    ]
    request.session[ACCOUNT_ACTIVE_USER_IDS_SESSION_KEY] = [
        user_id for user_id in verified_user_ids if user_id in normalized_user_ids
    ]


def get_session_account_group(request: HttpRequest) -> AccountGroup | None:
    """セッションまたは認証済みユーザーからアカウントグループを取得する。"""
    if request.user.is_authenticated:
        return remember_authenticated_account(request, request.user)

    group_id = request.session.get(ACCOUNT_GROUP_SESSION_KEY)
    if not group_id:
        return None

    return AccountGroup.objects.filter(pk=group_id).first()


def get_active_account_user_ids(request: HttpRequest, group: AccountGroup) -> list[int]:
    """セッション上でログイン済みとして扱うユーザーIDを取得する。"""
    raw_user_ids = request.session.get(ACCOUNT_ACTIVE_USER_IDS_SESSION_KEY)
    if raw_user_ids is None:
        activate_group_accounts(request, group)
        raw_user_ids = request.session.get(ACCOUNT_ACTIVE_USER_IDS_SESSION_KEY, [])
    return [int(user_id) for user_id in raw_user_ids]


def get_account_memberships(request: HttpRequest) -> list[AccountMembership]:
    """現在のセッションで連携済みの認証済みアカウント所属一覧を返す。"""
    group = get_session_account_group(request)
    if group is None:
        return []

    return get_related_memberships(group)


def get_active_memberships(request: HttpRequest) -> list[AccountMembership]:
    """現在のセッションでパスワードなしに切替可能なアカウント所属一覧を返す。"""
    group = get_session_account_group(request)
    if group is None:
        return []

    active_user_ids = get_active_account_user_ids(request, group)
    if not active_user_ids:
        return []

    return [
        membership for membership in get_related_memberships(group)
        if membership.user_id in active_user_ids
    ]


def deactivate_current_account(request: HttpRequest, user: AbstractBaseUser) -> list[AccountMembership]:
    """現在のアカウントだけをログアウト済みにする。"""
    group = ensure_account_group(user)
    remember_account_group(request, group)
    active_user_ids = get_active_account_user_ids(request, group)
    active_user_ids = [user_id for user_id in active_user_ids if user_id != user.pk]
    request.session[ACCOUNT_ACTIVE_USER_IDS_SESSION_KEY] = active_user_ids
    return [
        membership for membership in get_related_memberships(group)
        if membership.user_id in active_user_ids
    ]


@transaction.atomic
def remove_account_from_group(
    current_user: AbstractBaseUser,
    target_user: AbstractBaseUser,
    request: HttpRequest | None = None,
) -> bool:
    """現在ユーザーと対象ユーザーの連携を解除する。

    親子リンクがあればリンクを削除する。同一グループ所属（旧仕様データ）の
    場合は対象を新しいグループへ分離する。
    """
    if current_user.pk == target_user.pk:
        return False

    group = ensure_account_group(current_user)

    try:
        target_membership = target_user.account_membership
    except AccountMembership.DoesNotExist:
        return False

    target_group = target_membership.group
    if target_group.pk == group.pk:
        # 旧仕様の同一グループ所属: 対象を新しい単独グループへ分離する
        new_group = AccountGroup.objects.create()
        AccountMembership.objects.filter(pk=target_membership.pk).update(group=new_group)
        removed = True
    else:
        deleted, _ = AccountGroupLink.objects.filter(
            Q(parent=group, child=target_group) | Q(parent=target_group, child=group)
        ).delete()
        removed = deleted > 0

    if removed and request is not None:
        active_user_ids = get_active_account_user_ids(request, group)
        request.session[ACCOUNT_ACTIVE_USER_IDS_SESSION_KEY] = [
            user_id for user_id in active_user_ids if user_id != target_user.pk
        ]
    return removed


def record_login_success(user: AbstractBaseUser, request: HttpRequest) -> None:
    """ログイン成功時の処理（履歴記録・ユーザー情報更新）"""
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')

    history = LoginHistory.objects.create(
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
        success=True,
    )
    schedule_location_resolution(history)

    user.last_login_at = timezone.now()
    user.login_attempt_count += 1
    user.access_count += 1
    user.save(update_fields=['last_login_at', 'login_attempt_count', 'access_count'])


def record_login_failure(email: str | None, request: HttpRequest) -> None:
    """ログイン失敗時の処理（履歴記録・試行回数更新）"""
    User = get_user_model()

    try:
        user = User.objects.get(email=email)
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')

        history = LoginHistory.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
        )
        schedule_location_resolution(history)

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
