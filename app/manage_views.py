"""管理者パネル用ビュー（スタッフ・スーパーユーザー専用）"""
import json
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncMonth

from .models import ActivityLog, ContactMessage

import logging
logger = logging.getLogger(__name__)


def superuser_required(view_func):  # type: ignore[misc]
    """スーパーユーザー専用デコレータ"""
    @login_required
    def wrapper(request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        if not request.user.is_superuser:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


@superuser_required
def manage_dashboard(request: HttpRequest) -> HttpResponse:
    """管理パネル ダッシュボード"""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    total_users = User.objects.count()
    verified_users = User.objects.filter(is_email_verified=True).count()
    open_contacts = ContactMessage.objects.filter(status='open').count()
    in_progress_contacts = ContactMessage.objects.filter(status='in_progress').count()
    recent_contacts = ContactMessage.objects.select_related('user').order_by('-created_at')[:5]

    context = {
        'total_users': total_users,
        'verified_users': verified_users,
        'open_contacts': open_contacts,
        'in_progress_contacts': in_progress_contacts,
        'recent_contacts': recent_contacts,
    }
    return render(request, 'app/manage/dashboard.html', context)


@superuser_required
def manage_contacts(request: HttpRequest) -> HttpResponse:
    """問い合わせ管理一覧"""
    status_filter = request.GET.get('status', '')
    inquiry_filter = request.GET.get('inquiry_type', '')

    qs = ContactMessage.objects.select_related('user').order_by('-created_at')
    if status_filter:
        qs = qs.filter(status=status_filter)
    if inquiry_filter:
        qs = qs.filter(inquiry_type=inquiry_filter)

    context = {
        'contacts': qs,
        'status_filter': status_filter,
        'inquiry_filter': inquiry_filter,
        'status_choices': ContactMessage.STATUS_CHOICES,
        'inquiry_choices': ContactMessage.INQUIRY_TYPE_CHOICES,
    }
    return render(request, 'app/manage/contacts.html', context)


@superuser_required
def manage_contact_update(request: HttpRequest, contact_id: int) -> HttpResponse:
    """問い合わせのステータス更新・返信"""
    contact = get_object_or_404(ContactMessage, id=contact_id)

    if request.method == 'POST':
        new_status = request.POST.get('status', contact.status)
        reply_text = request.POST.get('admin_reply', '').strip()
        send_reply_email = request.POST.get('send_email') == '1'

        if new_status in dict(ContactMessage.STATUS_CHOICES):
            contact.status = new_status
            contact.is_resolved = (new_status == 'resolved')

        if reply_text:
            contact.admin_reply = reply_text
            contact.admin_reply_at = timezone.now()

            if send_reply_email and contact.user.email:
                try:
                    subject = f"【Re: {contact.subject}】お問い合わせへの返信"
                    body = f"""\
{contact.user.username} 様

お問い合わせいただきありがとうございます。
以下の通りご回答いたします。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【お問い合わせ内容】
{contact.message}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【返信内容】
{reply_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
このメールはシステムから自動送信されています。
"""
                    send_mail(
                        subject=subject,
                        message=body,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[contact.user.email],
                        fail_silently=False,
                    )
                    messages.success(request, '返信メールを送信しました。')
                except Exception as e:
                    logger.error(f"返信メール送信エラー: {e}")
                    messages.warning(request, '返信は保存されましたが、メール送信に失敗しました。')

        contact.save()
        messages.success(request, '問い合わせを更新しました。')
        return redirect('manage_contacts')

    context = {'contact': contact, 'status_choices': ContactMessage.STATUS_CHOICES}
    return render(request, 'app/manage/contact_detail.html', context)


@superuser_required
def manage_users(request: HttpRequest) -> HttpResponse:
    """ユーザー統計ページ"""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    total_users = User.objects.count()
    verified_users = User.objects.filter(is_email_verified=True).count()
    recent_users = User.objects.order_by('-created_at')[:20]

    context = {
        'total_users': total_users,
        'verified_users': verified_users,
        'recent_users': recent_users,
    }
    return render(request, 'app/manage/users.html', context)


@superuser_required
def manage_analytics(request: HttpRequest) -> HttpResponse:
    """機能使用率・アクセス分析ページ"""
    days = min(int(request.GET.get('days', '30')), 365)
    since = timezone.now() - timedelta(days=days)

    page_labels = {
        "expenses": "家計簿",
        "tasks": "タスク",
        "memos": "メモ",
        "shopping": "買うものリスト",
        "habits": "習慣トラッカー",
        "demo": "デモ",
    }
    action_labels = {
        "view": "閲覧",
        "create": "追加",
        "edit": "編集",
        "delete": "削除",
        "toggle": "切替",
    }

    base_qs = ActivityLog.objects.filter(accessed_at__gte=since)

    # 機能ごと × アクション種別の集計
    page_action_counts = (
        base_qs
        .values("page", "action")
        .annotate(count=Count("id"))
        .order_by("page", "action")
    )

    # 機能別に整形
    pages_data: dict[str, dict[str, object]] = {}
    for row in page_action_counts:
        page = row["page"]
        action = row["action"]
        if page not in pages_data:
            pages_data[page] = {
                "label": page_labels.get(page, page),
                "total": 0,
                "actions": {},
            }
        pages_data[page]["actions"][action] = row["count"]  # type: ignore[index]
        pages_data[page]["total"] = int(pages_data[page]["total"]) + row["count"]  # type: ignore[index]

    # 全機能の総アクセス数
    total_logs = base_qs.count()

    context = {
        "days": days,
        "total_logs": total_logs,
        "pages_data": pages_data,
        "page_labels": page_labels,
        "action_labels": action_labels,
    }
    return render(request, "app/manage/analytics.html", context)


@superuser_required
def manage_analytics_api(request: HttpRequest) -> JsonResponse:
    """分析データ JSON API（Chart.js 用）"""
    days = min(int(request.GET.get('days', '30')), 365)
    page_filter = request.GET.get('page', '')
    since = timezone.now() - timedelta(days=days - 1)

    qs = ActivityLog.objects.filter(accessed_at__gte=since)
    if page_filter:
        qs = qs.filter(page=page_filter)

    counts = (
        qs
        .annotate(date=TruncDate('accessed_at'))
        .values('date', 'page', 'action')
        .annotate(count=Count('id'))
        .order_by('date', 'page', 'action')
    )

    # date → {page_action: count} の辞書に変換
    data: dict[str, dict[str, int]] = {}
    for row in counts:
        date_str = str(row['date'])
        key = f"{row['page']}_{row['action']}"
        if date_str not in data:
            data[date_str] = {}
        data[date_str][key] = row['count']

    labels = sorted(data.keys())
    return JsonResponse({"labels": labels, "data": data})


@superuser_required
def manage_users_stats_api(request: HttpRequest) -> JsonResponse:
    """ユーザー登録統計 JSON API（Chart.js 用）"""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    period = request.GET.get('period', 'daily')   # 'daily' or 'monthly'
    verified_only = request.GET.get('verified_only', '0') == '1'
    days = min(int(request.GET.get('days', '30')), 365)

    now = timezone.now()
    qs = User.objects.all()
    if verified_only:
        qs = qs.filter(is_email_verified=True)

    if period == 'monthly':
        start = now - timedelta(days=days * 30 // 30)
        # 直近 N ヶ月
        months = max(1, days // 30)
        start = now.replace(day=1) - timedelta(days=31 * (months - 1))
        counts = (
            qs.filter(created_at__gte=start)
            .annotate(period=TruncMonth('created_at'))
            .values('period')
            .annotate(count=Count('id'))
            .order_by('period')
        )
        labels = [str(r['period'])[:7] for r in counts]
        new_counts = [r['count'] for r in counts]
    else:
        start = now - timedelta(days=days - 1)
        counts = (
            qs.filter(created_at__gte=start)
            .annotate(period=TruncDate('created_at'))
            .values('period')
            .annotate(count=Count('id'))
            .order_by('period')
        )
        labels = [str(r['period']) for r in counts]
        new_counts = [r['count'] for r in counts]

    # 累計ユーザー数（各日時点）
    total_counts: list[int] = []
    for label in labels:
        if period == 'monthly':
            cutoff = label + '-01'
        else:
            cutoff = label
        base_qs = User.objects.filter(created_at__date__lte=cutoff)
        if verified_only:
            base_qs = base_qs.filter(is_email_verified=True)
        total_counts.append(base_qs.count())

    return JsonResponse({
        'labels': labels,
        'new_counts': new_counts,
        'total_counts': total_counts,
    })
