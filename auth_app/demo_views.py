"""デモ画面用ビュー。ログイン不要でフェイクデータを使って各機能を表示する。"""
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect

from . import demo_data


def demo_redirect(request: HttpRequest) -> HttpResponse:
    return redirect('demo_expenses')


def demo_expenses(request: HttpRequest) -> HttpResponse:
    context = demo_data.get_expenses_context()
    context['is_demo'] = True
    return render(request, 'app/expenses/list.html', context)


def demo_tasks(request: HttpRequest) -> HttpResponse:
    context = demo_data.get_tasks_context()
    context['is_demo'] = True
    context['demo_day_tasks_json'] = demo_data.get_demo_day_tasks_json()
    return render(request, 'app/task/list.html', context)


def demo_habits(request: HttpRequest) -> HttpResponse:
    context = demo_data.get_habits_context()
    context['is_demo'] = True
    context['demo_habit_status_json'] = demo_data.get_demo_habit_status_json()
    context['demo_heatmap_json'] = demo_data.get_demo_heatmap_json()
    return render(request, 'app/habit/dashboard.html', context)


def demo_memos(request: HttpRequest) -> HttpResponse:
    context = demo_data.get_memos_context()
    context['is_demo'] = True
    return render(request, 'app/memo/list.html', context)


def demo_shopping(request: HttpRequest) -> HttpResponse:
    context = demo_data.get_shopping_context()
    context['is_demo'] = True
    return render(request, 'app/shopping/list.html', context)


def demo_board(request: HttpRequest) -> HttpResponse:
    context = {
        'is_demo': True,
        'demo_board_sets_json': demo_data.get_demo_board_sets_json(),
        'demo_board_tasks_json': demo_data.get_demo_board_tasks_json(),
    }
    return render(request, 'app/task/board.html', context)


def demo_expenses_settings(request: HttpRequest) -> HttpResponse:
    context = demo_data.get_expenses_settings_context()
    context['is_demo'] = True
    return render(request, 'app/expenses/settings.html', context)


def demo_task_settings(request: HttpRequest) -> HttpResponse:
    context = demo_data.get_task_settings_context()
    context['is_demo'] = True
    return render(request, 'app/task/settings.html', context)


def demo_memo_settings(request: HttpRequest) -> HttpResponse:
    context = demo_data.get_memo_settings_context()
    context['is_demo'] = True
    return render(request, 'app/memo/settings.html', context)


def demo_habit_list(request: HttpRequest) -> HttpResponse:
    context = demo_data.get_habit_list_context()
    context['is_demo'] = True
    return render(request, 'app/habit/list.html', context)


def demo_recurring_payments(request: HttpRequest) -> HttpResponse:
    context = demo_data.get_recurring_payments_context()
    context['is_demo'] = True
    return render(request, 'app/expenses/recurring_list.html', context)
