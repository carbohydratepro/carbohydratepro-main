"""ログからの重複しないイベント取り込み。送信処理とは独立する。"""
import hashlib
import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .log_monitoring import log_paths
from .security_models import SecurityEvent, SecurityMonitorState
from .security_rules import HOST_CATEGORIES, HOST_CRITICAL, LABELS, parse_application_line


def collect_events(now: datetime | None = None) -> None:
    now = now or timezone.now()
    SecurityMonitorState.objects.get_or_create(name='application')
    try:
        with transaction.atomic():
            state = SecurityMonitorState.objects.select_for_update().get(name='application')
            start = (state.checked_at - timedelta(minutes=10)) if state.checked_at else now - timedelta(hours=24)
            start = max(start, now - timedelta(days=settings.SECURITY_EVENT_RETENTION_DAYS))
            pending = []
            duplicates = Counter()

            def add(source, identity, occurred, category, severity):
                # ホスト停止中もアプリは進むため、遅れて届くSSH記録は保持期間内を再読する。
                earliest = now - timedelta(days=settings.SECURITY_EVENT_RETENTION_DAYS) if source == 'host' else start
                if not earliest <= occurred <= now:
                    return
                fingerprint = hashlib.sha256(f'{source}:{identity}'.encode()).hexdigest()
                pending.append(SecurityEvent(fingerprint=fingerprint, occurred_at=occurred,
                    source=source, category=category, severity=severity, summary=LABELS[category]))
                if len(pending) >= 500:
                    SecurityEvent.objects.bulk_create(pending, ignore_conflicts=True)
                    pending.clear()

            for filename, source in [('security.log', 'security'), ('django_debug.log', 'app')]:
                for path in log_paths(Path(settings.BASE_DIR), filename):
                    with path.open(encoding='utf-8', errors='replace') as log:
                        for line in log:
                            parsed = parse_application_line(line, source)
                            if parsed is None or not start <= parsed[0] <= now:
                                continue
                            duplicates[(source, line)] += 1
                            add(source, f'{line}:{duplicates[(source, line)]}', *parsed)
            if settings.SECURITY_HOST_MONITOR_ENABLED:
                folder = Path(settings.SECURITY_HOST_MONITOR_DIR)
                heartbeat = json.loads((folder / 'heartbeat.json').read_text())
                stamp = datetime.fromisoformat(heartbeat['checked_at'])
                if timezone.is_naive(stamp) or stamp > now + timedelta(minutes=1):
                    raise ValueError('Invalid host monitor timestamp')
                host, _ = SecurityMonitorState.objects.get_or_create(name='host')
                host.checked_at = stamp
                host.error = '' if heartbeat.get('healthy') is True else 'サーバー監視処理に異常があります'
                host.save(update_fields=['checked_at', 'error'])
                for path in sorted(folder.glob('events.jsonl*')):
                    with path.open(encoding='utf-8') as log:
                        for line in log:
                            item = json.loads(line)
                            category = item['category']
                            occurred = datetime.fromisoformat(item['occurred_at'])
                            if category not in HOST_CATEGORIES or timezone.is_naive(occurred):
                                raise ValueError('Invalid host event')
                            add('host', item['id'], occurred, category,
                                'critical' if category in HOST_CRITICAL else 'warning')
            SecurityEvent.objects.bulk_create(pending, ignore_conflicts=True)
            if state.checked_at is None:
                state.started_at = start
            state.checked_at = now
            state.error = ''
            state.save(update_fields=['started_at', 'checked_at', 'error'])
            SecurityEvent.objects.filter(occurred_at__lt=now-timedelta(days=settings.SECURITY_EVENT_RETENTION_DAYS)).delete()
    except (OSError, ValueError, KeyError, TypeError):
        SecurityMonitorState.objects.filter(name='application').update(error='ログ取り込みに失敗しました。監視元を確認してください')
        raise
