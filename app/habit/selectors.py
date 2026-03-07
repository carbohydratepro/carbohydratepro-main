from datetime import date, timedelta
from typing import Any

from django.db.models import Case, IntegerField, QuerySet, Value, When

from .models import Habit, HabitRecord


def get_habits(user: Any) -> QuerySet[Habit]:
    """日 → 週 → 月 の順にソートして返す。"""
    return Habit.objects.filter(user=user, is_active=True).annotate(
        freq_order=Case(
            When(frequency='daily', then=Value(0)),
            When(frequency='weekly', then=Value(1)),
            When(frequency='monthly', then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        )
    ).order_by('freq_order', 'created_at')


def get_heatmap_data(
    user: Any,
    end_date: date | None = None,
    days: int = 365,
    year: int | None = None,
) -> dict[str, float]:
    """日付 -> スコアの辞書を返す。

    year が指定された場合はその年全体（1/1〜12/31）を対象にする。
    指定がない場合は直近 days 日を対象にする。
    記録があるが合計スコアが 0 の日付もキーとして含まれる（値=0）。
    """
    today = date.today()
    if year is not None:
        start_date = date(year, 1, 1)
        end_date = min(date(year, 12, 31), today)
    else:
        if end_date is None:
            end_date = today
        start_date = end_date - timedelta(days=days - 1)

    records = HabitRecord.objects.filter(
        habit__user=user,
        date__gte=start_date,
        date__lte=end_date,
    ).select_related('habit')

    # 記録がある日付はスコア 0 でもキーとして残す（score-zero 判定のため）
    daily_scores: dict[str, float] = {}
    for record in records:
        date_str = record.date.isoformat()
        coeff = record.coefficient if record.coefficient is not None else record.habit.coefficient
        signed = coeff if record.habit.is_positive else -coeff
        if date_str not in daily_scores:
            daily_scores[date_str] = 0.0
        daily_scores[date_str] += signed

    return daily_scores


def get_today_status(user: Any, target_date: date) -> list[dict[str, Any]]:
    """指定日の習慣とその達成状況を返す。"""
    habits = get_habits(user)
    records = {
        r.habit_id: r
        for r in HabitRecord.objects.filter(
            habit__user=user,
            date=target_date,
        ).select_related('habit')
    }

    result: list[dict[str, Any]] = []
    for habit in habits:
        record = records.get(habit.id)
        completed = record is not None
        used_coeff = record.coefficient if (record and record.coefficient is not None) else habit.coefficient
        result.append({
            'id': habit.id,
            'title': habit.title,
            'frequency': habit.get_frequency_display(),
            'coefficient': habit.signed_coefficient,
            'default_coefficient': habit.coefficient,
            'used_coefficient': used_coeff,
            'color': habit.color,
            'is_positive': habit.is_positive,
            'completed': completed,
        })
    return result


def get_week_data(user: Any, week_start: date) -> list[dict[str, Any]]:
    """週次ビュー用データを返す。"""
    habits = get_habits(user)
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    week_end = week_dates[-1]

    records_by_habit: dict[int, set[str]] = {}
    for r in HabitRecord.objects.filter(
        habit__user=user,
        date__gte=week_start,
        date__lte=week_end,
    ):
        records_by_habit.setdefault(r.habit_id, set()).add(r.date.isoformat())

    result: list[dict[str, Any]] = []
    for habit in habits:
        done_dates = records_by_habit.get(habit.id, set())
        days_done = [d.isoformat() in done_dates for d in week_dates]
        done_count = sum(days_done)
        goal = habit.weekly_goal
        result.append({
            'id': habit.id,
            'title': habit.title,
            'color': habit.color,
            'is_positive': habit.is_positive,
            'days': days_done,
            'done_count': done_count,
            'weekly_goal': goal,
            'goal_met': goal > 0 and done_count >= goal,
        })
    return result
