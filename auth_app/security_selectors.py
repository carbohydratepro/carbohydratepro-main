"""管理者向け監視集計。未収集期間をゼロ件と誤表示しない。"""
from datetime import timedelta
from django.conf import settings
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from .security_models import SecurityEvent, SecurityMonitorState


def security_dashboard():
    now = timezone.now()
    today = timezone.localdate(now)
    first = today - timedelta(days=29)
    state = SecurityMonitorState.objects.filter(name='application').first()
    rows = SecurityEvent.objects.filter(occurred_at__date__gte=first).annotate(
        day=TruncDate('occurred_at')).values('day', 'severity', 'category').annotate(count=Count('id'))
    by_day = {}
    for row in rows:
        values = by_day.setdefault(row['day'], {'critical': 0, 'error': 0, 'warning': 0, 'maintenance': 0})
        key = 'maintenance' if row['category'] == 'maintenance' else row['severity']
        if key in values:
            values[key] += row['count']
    days = []
    for index in range(30):
        day = first + timedelta(days=index)
        known = state is not None and state.checked_at is not None and timezone.localdate(state.started_at) <= day <= timezone.localdate(state.checked_at)
        values = by_day.get(day, {'critical': 0, 'error': 0, 'warning': 0, 'maintenance': 0})
        days.append({'date': day.isoformat(), **{k: v if known else None for k, v in values.items()}})
    host = SecurityMonitorState.objects.filter(name='host').first()
    return {'days': days, 'state': state, 'host_state': host,
        'stale': not state or not state.checked_at or state.checked_at < now-timedelta(minutes=5) or bool(state.error),
        'host_enabled': settings.SECURITY_HOST_MONITOR_ENABLED,
        'host_stale': not host or not host.checked_at or host.checked_at < now-timedelta(minutes=5) or bool(host.error),
        'urgent_enabled': settings.SEND_URGENT_SECURITY_EMAIL,
        'recent': SecurityEvent.objects.exclude(category='maintenance').order_by('-occurred_at')[:20]}
