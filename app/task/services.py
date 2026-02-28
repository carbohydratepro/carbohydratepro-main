from __future__ import annotations

from datetime import timedelta

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
