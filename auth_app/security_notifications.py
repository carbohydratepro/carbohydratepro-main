"""重大イベントの集約通知。同じ種類は60分間抑制し、失敗時は再試行する。"""
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import get_connection, send_mail
from django.db import transaction
from django.utils import timezone

from .security_models import SecurityAlertState, SecurityEvent, SecurityMonitorState
from .security_rules import LABELS


def urgent_candidates(now: datetime) -> dict[str, tuple[datetime, int, str, int]]:
    # 直近5分の障害集中と、未通知の重大イベント（停止後の再開も含む）を分ける。
    start, _ = SecurityMonitorState.objects.get_or_create(name='notifications', defaults={'started_at': now})
    since = start.started_at-timedelta(minutes=5)
    events = SecurityEvent.objects.filter(occurred_at__gte=since, occurred_at__lte=now)
    result = {}
    for category in events.filter(severity='critical').order_by().values_list('category', flat=True).distinct():
        group = events.filter(category=category, severity='critical')
        result[category] = (group.latest('occurred_at').occurred_at, group.count(), LABELS[category], group.latest('pk').pk)
    burst = events.filter(category='app_error', occurred_at__gte=now-timedelta(minutes=5))
    if burst.count() >= 10:
        result['app_error_burst'] = (burst.latest('occurred_at').occurred_at, burst.count(), LABELS['app_error_burst'], burst.latest('pk').pk)
    state = SecurityMonitorState.objects.filter(name='application').first()
    if state and state.error:
        result['collection_failure'] = (now, 1, 'ログ取り込みに失敗しています', 0)
    if settings.SECURITY_HOST_MONITOR_ENABLED:
        host = SecurityMonitorState.objects.filter(name='host').first()
        if not host or not host.checked_at or host.checked_at < now-timedelta(minutes=5) or host.error:
            result['host_monitor_stale'] = (now, 1, LABELS['host_monitor_stale'], 0)
    return result


def send_urgent_report(now: datetime | None = None) -> bool:
    if not settings.SEND_URGENT_SECURITY_EMAIL:
        return False
    now = now or timezone.now()
    candidates = urgent_candidates(now)
    since = SecurityMonitorState.objects.get(name='notifications').started_at - timedelta(minutes=5)
    # 固定順に行をロックし、複数cronからの同時送信を抑止する。
    for signature in sorted(candidates):
        SecurityAlertState.objects.get_or_create(signature=signature)
    with transaction.atomic():
        states = list(SecurityAlertState.objects.select_for_update().filter(
            signature__in=candidates).order_by('signature'))
        due = []
        for state in states:
            latest, count, label, event_id = candidates[state.signature]
            already_sent = event_id <= state.last_event_id if event_id else state.sent_at and latest <= state.sent_at
            if state.sent_at and (already_sent or
                now-state.sent_at < timedelta(minutes=settings.SECURITY_ALERT_COOLDOWN_MINUTES)):
                continue
            if event_id and state.signature != 'app_error_burst':
                count = SecurityEvent.objects.filter(category=state.signature, severity='critical',
                    occurred_at__gte=since, occurred_at__lte=now,
                    pk__gt=state.last_event_id, pk__lte=event_id).count()
            due.append((state, count, label, event_id))
        if not due:
            return False
        message = ['重要なセキュリティ・障害イベントを検出しました。',
            f'確認時刻: {timezone.localtime(now):%Y-%m-%d %H:%M:%S}', '']
        message += [f'- {label}: {count}件' for _, count, label, _ in due]
        message += ['', '検知は侵入確定を意味しません。管理パネルとサーバーログを確認してください。',
                    '同種の通知は60分間抑制します。その他の検出内容は日次レポートへ集約します。']
        delivered = send_mail(subject='【要確認】重要なセキュリティ・障害イベント',
            message='\n'.join(message), from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.SECURITY_ALERT_EMAIL], fail_silently=False,
            connection=get_connection(timeout=15))
        if delivered != 1:
            raise RuntimeError('Urgent security report was not accepted by mail backend')
        for state, _, _, event_id in due:
            state.sent_at = now
            state.last_event_id = event_id
            state.save(update_fields=['sent_at', 'last_event_id'])
        return True
