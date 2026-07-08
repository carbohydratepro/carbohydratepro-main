from __future__ import annotations

import calendar
from datetime import date, datetime
from datetime import timezone as dt_timezone
from typing import TYPE_CHECKING

from django.db.models import Q, QuerySet
from django.utils.timezone import localtime, make_aware

from .models import ExternalEvent, Task, TaskLabel

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser


def get_external_events(
    user: AbstractBaseUser,
    range_start: datetime,
    range_end: datetime,
) -> list[ExternalEvent]:
    """範囲内の外部カレンダーイベントを取得（読み取り専用表示用）"""
    return list(
        ExternalEvent.objects.filter(
            calendar__user=user,
            start_date__lte=range_end,
        ).filter(
            Q(end_date__gte=range_start) |
            Q(end_date__isnull=True, start_date__gte=range_start)
        ).select_related('calendar').order_by('start_date')
    )


# start_date が未設定の項目をソート末尾に回すための番兵値
_FAR_FUTURE = datetime(9999, 1, 1, tzinfo=dt_timezone.utc)


def merge_tasks_and_external_events(
    tasks: list,
    external_events: list[ExternalEvent],
) -> list:
    """タスクと外部イベントを表示順（終日→開始時刻）にマージする"""
    combined = list(tasks) + list(external_events)
    combined.sort(key=lambda item: (not item.all_day, item.start_date or _FAR_FUTURE))
    return combined


def get_day_view_tasks(user: AbstractBaseUser, day_start: datetime, day_end: datetime) -> QuerySet:
    """日表示用タスク一覧を取得"""
    return Task.objects.filter(
        user=user,
        parent_task__isnull=True,
    ).filter(
        Q(start_date__lte=day_end, end_date__gte=day_start) |
        Q(start_date__lte=day_end, end_date__isnull=True) |
        Q(start_date__isnull=True, end_date__gte=day_start)
    ).select_related('label')


def apply_filters(
    tasks_qs: QuerySet,
    status_filter: str,
    priority_filter: str,
    search_query: str,
) -> QuerySet:
    """タスククエリセットにフィルターを適用"""
    if status_filter:
        tasks_qs = tasks_qs.filter(status=status_filter)
    if priority_filter:
        tasks_qs = tasks_qs.filter(priority=priority_filter)
    if search_query:
        tasks_qs = tasks_qs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    return tasks_qs


def build_gantt_data(tasks_qs: QuerySet, day_start: datetime, day_end: datetime) -> list[dict[str, object]]:
    """ガントチャート用データを生成"""
    gantt_data: list[dict[str, object]] = []
    for task in tasks_qs:
        if task.all_day:
            gantt_data.append({
                'task': task,
                'start_percent': 0,
                'width_percent': 100,
                'start_time': '終日',
                'end_time': '',
                'is_all_day': True,
            })
            continue

        task_start = task.start_date if task.start_date else day_start
        task_end = task.end_date if task.end_date else day_end
        display_start = localtime(max(task_start, day_start))
        display_end = localtime(min(task_end, day_end))

        start_minutes = display_start.hour * 60 + display_start.minute
        end_minutes = display_end.hour * 60 + display_end.minute
        start_percent = (start_minutes / 1440) * 100
        end_percent = (end_minutes / 1440) * 100
        width_percent = max(end_percent - start_percent, 1)

        gantt_data.append({
            'task': task,
            'start_percent': start_percent,
            'width_percent': width_percent,
            'start_time': display_start.strftime('%H:%M'),
            'end_time': display_end.strftime('%H:%M'),
            'is_all_day': False,
        })
    return gantt_data


def get_all_user_tasks(user: AbstractBaseUser) -> QuerySet:
    """ユーザーの全親タスクを取得"""
    return Task.objects.filter(
        user=user,
        parent_task__isnull=True,
    ).select_related('label')


def get_month_tasks(user: AbstractBaseUser, start_date: datetime, end_date: datetime) -> QuerySet:
    """月表示用の月範囲内タスクを取得"""
    return Task.objects.filter(
        user=user,
        parent_task__isnull=True,
    ).filter(
        Q(start_date__range=(start_date, end_date)) |
        Q(end_date__range=(start_date, end_date)) |
        Q(start_date__lte=start_date, end_date__gte=end_date)
    ).select_related('label')


def build_calendar_data(
    month_tasks: QuerySet,
    year: int,
    month: int,
    week_start: str,
    external_events: list[ExternalEvent] | None = None,
) -> tuple[list[list[dict[str, object]]], list[str]]:
    """カレンダーデータと曜日ラベルを生成（外部イベントも日別にマージする）"""
    firstweekday = 6 if week_start == 'sunday' else 0
    cal = calendar.Calendar(firstweekday=firstweekday).monthdatescalendar(year, month)
    weekday_labels = (
        ['日', '月', '火', '水', '木', '金', '土']
        if week_start == 'sunday'
        else ['月', '火', '水', '木', '金', '土', '日']
    )
    external_events = external_events or []

    today = date.today()
    calendar_data: list[list[dict[str, object]]] = []
    for week in cal:
        week_data: list[dict[str, object]] = []
        for d in week:
            is_current_month = (d.month == month)
            is_today = (d == today)
            day_start = make_aware(datetime(d.year, d.month, d.day, 0, 0, 0))
            day_end = make_aware(datetime(d.year, d.month, d.day, 23, 59, 59))
            day_tasks = list(month_tasks.filter(
                Q(start_date__lte=day_end, end_date__gte=day_start) |
                Q(start_date__lte=day_end, end_date__isnull=True) |
                Q(start_date__isnull=True, end_date__gte=day_start)
            ).order_by('start_date'))
            day_externals = [
                event for event in external_events
                if event.start_date <= day_end and (event.end_date or event.start_date) >= day_start
            ]
            day_items = merge_tasks_and_external_events(day_tasks, day_externals)
            week_data.append({
                'day': d.day,
                'month': d.month,
                'year': d.year,
                'tasks': day_items[:5],
                'task_count': len(day_items),
                'is_current_month': is_current_month,
                'is_today': is_today,
            })
        calendar_data.append(week_data)
    return calendar_data, weekday_labels


def build_task_api_json(tasks: QuerySet) -> list[dict[str, object]]:
    """APIレスポンス用タスクデータを構築"""
    tasks_data: list[dict[str, object]] = []
    for task in tasks:
        local_start = localtime(task.start_date) if task.start_date else None
        local_end = localtime(task.end_date) if task.end_date else None
        if task.all_day:
            date_display = local_start.strftime('%Y-%m-%d') if local_start else ''
            if local_end and local_start and local_start.date() != local_end.date():
                date_display += f" 〜 {local_end.strftime('%Y-%m-%d')}"
        else:
            date_display = local_start.strftime('%Y-%m-%d %H:%M') if local_start else ''
            if local_end and local_start:
                if local_start.date() == local_end.date():
                    date_display += f" 〜 {local_end.strftime('%H:%M')}"
                else:
                    date_display += f" 〜 {local_end.strftime('%Y-%m-%d %H:%M')}"

        tasks_data.append({
            'id': task.id,
            'title': task.title,
            'description': task.description[:100] if task.description else '',
            'status': task.status,
            'status_display': task.get_status_display(),
            'priority': task.priority,
            'priority_display': task.get_priority_display(),
            'due_date': date_display,
            'label': {
                'id': task.label.id,
                'name': task.label.name,
                'color': task.label.color,
            } if task.label else None,
        })
    return tasks_data


def build_external_api_json(external_events: list[ExternalEvent]) -> list[dict[str, object]]:
    """APIレスポンス用の外部イベントデータを構築（読み取り専用）"""
    events_data: list[dict[str, object]] = []
    for event in external_events:
        local_start = localtime(event.start_date)
        local_end = localtime(event.end_date) if event.end_date else None
        if event.all_day:
            date_display = local_start.strftime('%Y-%m-%d')
            if local_end and local_start.date() != local_end.date():
                date_display += f" 〜 {local_end.strftime('%Y-%m-%d')}"
        else:
            date_display = local_start.strftime('%Y-%m-%d %H:%M')
            if local_end:
                if local_start.date() == local_end.date():
                    date_display += f" 〜 {local_end.strftime('%H:%M')}"
                else:
                    date_display += f" 〜 {local_end.strftime('%Y-%m-%d %H:%M')}"

        events_data.append({
            'is_external': True,
            'title': event.title,
            'due_date': date_display,
            'calendar': {
                'name': event.calendar.name,
                'color': event.calendar.color,
            },
        })
    return events_data


def get_labels(user: AbstractBaseUser) -> QuerySet:
    """ユーザーのラベル一覧を取得"""
    return TaskLabel.objects.filter(user=user)
