from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone

from django.core.exceptions import ValidationError

from .models import MAX_REPEAT_COUNT, MAX_REPEAT_INTERVAL, Task


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
    if interval > MAX_REPEAT_INTERVAL or count > MAX_REPEAT_COUNT:
        raise ValidationError('繰り返し間隔または回数が上限を超えています。')

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
    from urllib.parse import urlsplit

    url = url.strip()
    if url.lower().startswith('webcal://'):
        url = 'https://' + url[len('webcal://'):]
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise ValueError('http または https のURLを指定してください。')
    if parsed.username is not None or parsed.password is not None:
        raise ValueError('認証情報を含むURLは指定できません。')
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError('ポート番号が不正です。') from exc
    expected_port = 443 if parsed.scheme == 'https' else 80
    if port is not None and port != expected_port:
        raise ValueError('標準ポート以外のURLは指定できません。')
    return url


def _resolve_public_ip(hostname: str, port: int) -> str:
    """ホストを検証し、接続に固定するグローバルIPを返す。

    プライベート/ループバック/リンクローカル/予約済みIP（AWSメタデータ等）
    へのアクセスを拒否する。検証後の再名前解決を避けるため、呼び出し元は
    戻り値のIPへ直接接続する。
    """
    import ipaddress
    import socket

    try:
        infos = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError('ホスト名を解決できませんでした。') from exc
    addresses: list[str] = []
    for info in infos:
        address = info[4][0]
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ValueError('このURLへのアクセスは許可されていません。')
        if address not in addresses:
            addresses.append(address)
    if not addresses:
        raise ValueError('ホスト名を解決できませんでした。')
    return addresses[0]


def _assert_public_host(hostname: str) -> None:
    """URL入力時の事前検証用ラッパー。"""
    _resolve_public_ip(hostname, 443)


def _request_pinned_url(url: str, pinned_ip: str) -> tuple[int, Mapping[str, str], bytes]:
    """検証済みIPへ直接接続して、応答をサイズ制限付きで取得する。"""
    from urllib.parse import urlsplit, urlunsplit

    import requests
    import urllib3

    parsed = urlsplit(url)
    hostname = parsed.hostname or ''
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    timeout = urllib3.Timeout(
        connect=EXTERNAL_FETCH_TIMEOUT_SECONDS,
        read=EXTERNAL_FETCH_TIMEOUT_SECONDS,
    )
    if parsed.scheme == 'https':
        pool = urllib3.HTTPSConnectionPool(
            pinned_ip,
            port=port,
            timeout=timeout,
            maxsize=1,
            block=True,
            cert_reqs='CERT_REQUIRED',
            ca_certs=requests.certs.where(),
            assert_hostname=hostname,
            server_hostname=hostname,
        )
    else:
        pool = urllib3.HTTPConnectionPool(
            pinned_ip,
            port=port,
            timeout=timeout,
            maxsize=1,
            block=True,
        )

    response = None
    try:
        request_target = urlunsplit(('', '', parsed.path or '/', parsed.query, ''))
        response = pool.urlopen(
            'GET',
            request_target,
            headers={
                'Host': parsed.netloc,
                'User-Agent': 'carbohydratepro-calendar-sync/1.0',
                'Accept-Encoding': 'identity',
            },
            redirect=False,
            retries=False,
            preload_content=False,
        )
        content = b''
        if response.status not in (301, 302, 303, 307, 308):
            for chunk in response.stream(64 * 1024):
                content += chunk
                if len(content) > EXTERNAL_MAX_ICS_BYTES:
                    raise ValueError('ICSファイルが大きすぎます（5MB上限）。')
        return response.status, response.headers, content
    finally:
        if response is not None:
            response.close()
        pool.close()


def fetch_external_ics(url: str) -> bytes:
    """外部カレンダーのICSを取得する（リダイレクトごとにURLを再検証）。"""
    from urllib.parse import urljoin, urlsplit

    for _ in range(EXTERNAL_MAX_REDIRECTS + 1):
        url = normalize_external_calendar_url(url)
        parsed = urlsplit(url)
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        pinned_ip = _resolve_public_ip(parsed.hostname or '', port)
        status, headers, content = _request_pinned_url(url, pinned_ip)
        if status in (301, 302, 303, 307, 308):
            location = headers.get('Location')
            if not location:
                raise ValueError('不正なリダイレクト応答を受信しました。')
            url = urljoin(url, location)
            continue
        if status < 200 or status >= 300:
            raise ValueError(f'カレンダーの取得に失敗しました（HTTP {status}）。')
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
    pages = recurring_ical_events.of(ical).paginate(
        EXTERNAL_MAX_EVENTS,
        range_start,
        range_end,
    )
    occurrences = next(iter(pages), ())

    events: list[ExternalEvent] = []
    for component in occurrences:
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
