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
