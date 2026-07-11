"""統合ダッシュボード（ログイン後のホーム画面）"""
from __future__ import annotations

from datetime import datetime, time, timedelta
from decimal import Decimal
from typing import Any

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.timezone import make_aware

from .expenses.models import Transaction
from .habit import selectors as habit_selectors
from .memo.models import Memo
from .shopping.models import ShoppingItem
from .task import selectors as task_selectors

DASHBOARD_TASK_LIMIT = 6
DASHBOARD_SHOPPING_LIMIT = 5
DASHBOARD_MEMO_LIMIT = 3


def build_dashboard_context(user: Any) -> dict[str, Any]:
    """ダッシュボード表示用のコンテキストを構築する。"""
    today = timezone.localdate()
    day_start = make_aware(datetime.combine(today, time.min))
    day_end = make_aware(datetime.combine(today, time.max))

    # 今日のタスク（外部カレンダーのイベントもマージ）
    today_tasks_qs = (
        task_selectors.get_day_view_tasks(user, day_start, day_end)
        .order_by('-all_day', 'start_date')
    )
    today_externals = task_selectors.get_external_events(user, day_start, day_end)
    today_items = task_selectors.merge_tasks_and_external_events(
        list(today_tasks_qs), today_externals,
    )
    today_tasks_count = len(today_items)
    today_tasks = today_items[:DASHBOARD_TASK_LIMIT]

    # 今日の習慣
    habit_status = habit_selectors.get_today_status(user, today)
    habits_completed = sum(1 for habit in habit_status if habit['completed'])

    # 今月の収支
    month_start = make_aware(datetime(today.year, today.month, 1))
    next_month = (month_start + timedelta(days=32)).replace(day=1)
    month_transactions = Transaction.objects.filter(
        user=user, date__gte=month_start, date__lt=next_month,
    )
    income_total = (
        month_transactions.filter(transaction_type='income')
        .aggregate(total=Sum('amount'))['total'] or Decimal('0')
    )
    expense_total = (
        month_transactions.filter(transaction_type='expense')
        .aggregate(total=Sum('amount'))['total'] or Decimal('0')
    )

    # 今月の予算消化（全体予算が設定されている場合のみカード表示）
    from .expenses import selectors as expense_selectors
    budget_overview = expense_selectors.build_budget_overview(user, today.year, today.month)

    # 買い物リスト（未購入）
    shopping_qs = ShoppingItem.objects.filter(user=user, is_checked=False)
    shopping_count = shopping_qs.count()
    shopping_insufficient_count = shopping_qs.filter(status='insufficient').count()
    shopping_items = list(shopping_qs[:DASHBOARD_SHOPPING_LIMIT])

    # 最近のメモ
    recent_memos = list(
        Memo.objects.filter(user=user)
        .select_related('memo_type')
        .order_by('-updated_date')[:DASHBOARD_MEMO_LIMIT]
    )

    return {
        'today': today,
        'today_tasks': today_tasks,
        'today_tasks_count': today_tasks_count,
        'habit_status': habit_status,
        'habits_completed': habits_completed,
        'habits_total': len(habit_status),
        'income_total': income_total,
        'expense_total': expense_total,
        'balance_total': income_total - expense_total,
        'target_month': today.strftime('%Y年%m月'),
        'budget_overall': budget_overview['overall'],
        'budget_over_count': budget_overview['over_count'],
        'shopping_items': shopping_items,
        'shopping_count': shopping_count,
        'shopping_insufficient_count': shopping_insufficient_count,
        'recent_memos': recent_memos,
    }


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """統合ダッシュボードを表示する。"""
    context = build_dashboard_context(request.user)
    return render(request, 'app/dashboard.html', context)
