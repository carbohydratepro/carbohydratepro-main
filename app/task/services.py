from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .models import Task


def create_recurring_tasks(parent_task: Task) -> None:
    """繰り返しタスクの子タスクを作成"""
    from dateutil.relativedelta import relativedelta

    if not parent_task.start_date:
        return

    frequency = parent_task.frequency
    interval = parent_task.repeat_interval or 1
    count = parent_task.repeat_count

    if not count or count <= 0:
        return

    current_start = parent_task.start_date
    current_end = parent_task.end_date

    for _ in range(count):
        if frequency == 'daily':
            next_start = current_start + timedelta(days=interval)
            next_end = current_end + timedelta(days=interval) if current_end else None
        elif frequency == 'weekly':
            next_start = current_start + timedelta(weeks=interval)
            next_end = current_end + timedelta(weeks=interval) if current_end else None
        elif frequency == 'monthly':
            next_start = current_start + relativedelta(months=interval)
            next_end = current_end + relativedelta(months=interval) if current_end else None
        elif frequency == 'yearly':
            next_start = current_start + relativedelta(years=interval)
            next_end = current_end + relativedelta(years=interval) if current_end else None
        else:
            break

        Task.objects.create(
            user=parent_task.user,
            title=parent_task.title,
            frequency='',
            repeat_interval=1,
            priority=parent_task.priority,
            status='not_started',
            label=parent_task.label,
            start_date=next_start,
            end_date=next_end,
            all_day=parent_task.all_day,
            description=parent_task.description,
            parent_task=parent_task,
        )

        current_start = next_start
        current_end = next_end


# ---------------------------------------------------------------------------
# ICSカレンダー配信
# ---------------------------------------------------------------------------

ICS_PAST_DAYS = 30
ICS_FUTURE_DAYS = 370


def _escape_ics_text(value: str) -> str:
    """RFC 5545のTEXT値エスケープ。"""
    return (
        value.replace('\\', '\\\\')
        .replace(';', '\\;')
        .replace(',', '\\,')
        .replace('\r\n', '\\n')
        .replace('\n', '\\n')
    )


def _fold_ics_line(line: str) -> str:
    """RFC 5545の75オクテット折り返し（継続行は先頭スペース）。"""
    encoded = line.encode('utf-8')
    if len(encoded) <= 75:
        return line

    parts: list[str] = []
    current = b''
    limit = 75
    for char in line:
        char_bytes = char.encode('utf-8')
        if len(current) + len(char_bytes) > limit:
            parts.append(current.decode('utf-8'))
            current = b' ' + char_bytes
            limit = 75
        else:
            current += char_bytes
    if current:
        parts.append(current.decode('utf-8'))
    return '\r\n'.join(parts)


def _format_ics_datetime(value: datetime) -> str:
    """aware datetimeをICSのUTC表記へ変換する。"""
    return value.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def build_calendar_feed(user: object) -> str:
    """ユーザーのタスクからICSカレンダーフィードを生成する。"""
    from django.conf import settings
    from django.utils import timezone as django_timezone

    now = django_timezone.now()
    range_start = now - timedelta(days=ICS_PAST_DAYS)
    range_end = now + timedelta(days=ICS_FUTURE_DAYS)

    tasks = (
        Task.objects
        .filter(
            user=user,
            parent_task__isnull=True,
            start_date__isnull=False,
            start_date__gte=range_start,
            start_date__lte=range_end,
        )
        .order_by('start_date')
    )

    domain = getattr(settings, 'SITE_DOMAIN', 'localhost')
    lines: list[str] = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Life management//Task Calendar//JA',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        'X-WR-CALNAME:Life management',
        'X-WR-TIMEZONE:Asia/Tokyo',
    ]

    dtstamp = _format_ics_datetime(now)
    for task in tasks:
        lines.append('BEGIN:VEVENT')
        lines.append(f'UID:task-{task.pk}@{domain}')
        lines.append(f'DTSTAMP:{dtstamp}')
        if task.all_day:
            start_date = django_timezone.localtime(task.start_date).date()
            end_source = task.end_date or task.start_date
            end_date = django_timezone.localtime(end_source).date()
            if end_date < start_date:
                end_date = start_date
            # 終日イベントのDTENDは翌日（RFC 5545の排他的終了）
            lines.append(f'DTSTART;VALUE=DATE:{start_date.strftime("%Y%m%d")}')
            lines.append(f'DTEND;VALUE=DATE:{(end_date + timedelta(days=1)).strftime("%Y%m%d")}')
        else:
            end_datetime = task.end_date or (task.start_date + timedelta(hours=1))
            lines.append(f'DTSTART:{_format_ics_datetime(task.start_date)}')
            lines.append(f'DTEND:{_format_ics_datetime(end_datetime)}')
        lines.append(f'SUMMARY:{_escape_ics_text(task.title)}')
        if task.description:
            lines.append(f'DESCRIPTION:{_escape_ics_text(task.description)}')
        lines.append(f'STATUS:{"COMPLETED" if task.status == "completed" else "CONFIRMED"}')
        lines.append('END:VEVENT')

    lines.append('END:VCALENDAR')
    return '\r\n'.join(_fold_ics_line(line) for line in lines) + '\r\n'


# ==========================================================================
# 外部カレンダー同期（ICS購読URLの取り込み）
# ==========================================================================

EXTERNAL_FETCH_TIMEOUT_SECONDS = 10
EXTERNAL_MAX_ICS_BYTES = 5 * 1024 * 1024
EXTERNAL_MAX_REDIRECTS = 3
EXTERNAL_MAX_EVENTS = 2000
# 取り込み範囲（配信側の build_calendar_feed と同じ幅）
EXTERNAL_SYNC_PAST_DAYS = 30
EXTERNAL_SYNC_FUTURE_DAYS = 370


def normalize_external_calendar_url(url: str) -> str:
    """外部カレンダーURLを正規化して検証する。

    webcal:// は https:// に変換する。http/https 以外は拒否する。
    """
    from urllib.parse import urlparse

    url = url.strip()
    if url.lower().startswith('webcal://'):
        url = 'https://' + url[len('webcal://'):]
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise ValueError('http または https のURLを指定してください。')
    return url


def _assert_public_host(hostname: str) -> None:
    """SSRF対策: ホストがグローバルIPに解決されることを確認する。

    プライベート/ループバック/リンクローカル/予約済みIP（AWSメタデータ等）
    へのアクセスを拒否する。
    """
    import ipaddress
    import socket

    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise ValueError('ホスト名を解決できませんでした。')
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise ValueError('このURLへのアクセスは許可されていません。')


def fetch_external_ics(url: str) -> bytes:
    """外部カレンダーのICSを取得する（リダイレクトごとにURLを再検証）。"""
    from urllib.parse import urljoin, urlparse

    import requests

    for _ in range(EXTERNAL_MAX_REDIRECTS + 1):
        url = normalize_external_calendar_url(url)
        _assert_public_host(urlparse(url).hostname or '')
        response = requests.get(
            url,
            timeout=EXTERNAL_FETCH_TIMEOUT_SECONDS,
            allow_redirects=False,
            stream=True,
            headers={'User-Agent': 'carbohydratepro-calendar-sync/1.0'},
        )
        if response.is_redirect or response.is_permanent_redirect:
            location = response.headers.get('Location')
            if not location:
                raise ValueError('不正なリダイレクト応答を受信しました。')
            url = urljoin(url, location)
            continue
        response.raise_for_status()
        content = b''
        for chunk in response.iter_content(chunk_size=64 * 1024):
            content += chunk
            if len(content) > EXTERNAL_MAX_ICS_BYTES:
                raise ValueError('ICSファイルが大きすぎます（5MB上限）。')
        return content
    raise ValueError('リダイレクトが多すぎます。')


def sync_external_calendar(external_calendar: 'ExternalCalendar') -> int:
    """外部カレンダーを同期し、取り込んだイベント数を返す。

    購読範囲（過去30日〜未来370日）のイベントを洗い替えする。
    繰り返し（RRULE）は recurring_ical_events で個別イベントに展開する。
    """
    from datetime import time as time_cls

    import recurring_ical_events
    from django.db import transaction
    from django.utils import timezone as django_timezone
    from icalendar import Calendar as ICalCalendar

    from .models import ExternalEvent

    now_local = django_timezone.localtime()
    range_start = now_local - timedelta(days=EXTERNAL_SYNC_PAST_DAYS)
    range_end = now_local + timedelta(days=EXTERNAL_SYNC_FUTURE_DAYS)

    content = fetch_external_ics(external_calendar.url)
    ical = ICalCalendar.from_ical(content)
    occurrences = recurring_ical_events.of(ical).between(range_start, range_end)

    events: list[ExternalEvent] = []
    for component in occurrences[:EXTERNAL_MAX_EVENTS]:
        dtstart = component.get('DTSTART')
        if dtstart is None:
            continue
        start = dtstart.dt
        dtend = component.get('DTEND')
        end = dtend.dt if dtend is not None else None

        all_day = not isinstance(start, datetime)
        if all_day:
            start = django_timezone.make_aware(datetime.combine(start, time_cls.min))
            if end is not None and not isinstance(end, datetime):
                # 終日イベントのDTENDは排他的（翌日）なので1秒引いて包含にする
                end = django_timezone.make_aware(datetime.combine(end, time_cls.min)) - timedelta(seconds=1)
            else:
                end = start + timedelta(days=1) - timedelta(seconds=1)
        else:
            if django_timezone.is_naive(start):
                start = django_timezone.make_aware(start)
            if end is not None and django_timezone.is_naive(end):
                end = django_timezone.make_aware(end)

        title = str(component.get('SUMMARY', '')).strip() or '（無題）'
        events.append(ExternalEvent(
            calendar=external_calendar,
            uid=str(component.get('UID', ''))[:500],
            title=title[:300],
            start_date=start,
            end_date=end,
            all_day=all_day,
        ))

    with transaction.atomic():
        external_calendar.events.all().delete()
        ExternalEvent.objects.bulk_create(events)
        external_calendar.last_synced_at = django_timezone.now()
        external_calendar.last_error = ''
        external_calendar.save(update_fields=['last_synced_at', 'last_error'])
    return len(events)


def sync_external_calendar_safe(external_calendar: 'ExternalCalendar') -> tuple[bool, str]:
    """外部カレンダーを同期し、失敗時はエラーを記録して (成否, メッセージ) を返す。"""
    try:
        count = sync_external_calendar(external_calendar)
        return True, f'{count}件のイベントを取り込みました。'
    except Exception as exc:  # noqa: BLE001 - cron/画面双方で失敗を握って記録する
        message = str(exc)[:200] or exc.__class__.__name__
        external_calendar.last_error = message
        external_calendar.save(update_fields=['last_error'])
        return False, message
