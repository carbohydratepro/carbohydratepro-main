import json
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import HabitForm
from .models import Habit, HabitRecord
from . import selectors


@login_required
def habit_dashboard(request: HttpRequest) -> HttpResponse:
    today = date.today()
    min_date = today - timedelta(days=6)

    # 日ビュー: 過去7日以内の日付を選択可能
    date_str = request.GET.get('date', today.isoformat())
    try:
        selected_date = date.fromisoformat(date_str)
        if selected_date > today or selected_date < min_date:
            selected_date = today
    except ValueError:
        selected_date = today

    # 年ビュー: 直近365日 or 指定年
    year_str = request.GET.get('year')
    selected_year: int | None = None
    if year_str:
        try:
            selected_year = int(year_str)
        except ValueError:
            selected_year = None

    habits = selectors.get_habits(request.user)
    today_status = selectors.get_today_status(request.user, selected_date)

    if selected_year:
        heatmap_data = selectors.get_heatmap_data(request.user, year=selected_year)
    else:
        heatmap_data = selectors.get_heatmap_data(request.user, end_date=today)

    # 週次ビュー
    dow = today.weekday()
    week_start = today - timedelta(days=dow)
    week_data = selectors.get_week_data(request.user, week_start)
    week_dates = [week_start + timedelta(days=i) for i in range(7)]

    # 年選択肢（今年 + 過去2年）
    year_choices = [today.year - i for i in range(3)]

    return render(request, 'app/habit/dashboard.html', {
        'habits': habits,
        'today_status': today_status,
        'heatmap_data_json': json.dumps(heatmap_data),
        'today': today.isoformat(),
        'min_date': min_date.isoformat(),
        'selected_date': selected_date.isoformat(),
        'selected_year': selected_year,
        'year_choices': year_choices,
        'form': HabitForm(),
        'week_data': week_data,
        'week_dates': [d.isoformat() for d in week_dates],
        'week_dates_display': [f'{d.month}/{d.day}' for d in week_dates],
        'week_header_data': [{'display': f'{d.month}/{d.day}', 'date': d.isoformat()} for d in week_dates],
    })


@login_required
def create_habit(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = HabitForm(request.POST)
        if form.is_valid():
            habit = form.save(commit=False)
            habit.user = request.user
            habit.save()
    return redirect('habit_dashboard')


@login_required
def edit_habit(request: HttpRequest, habit_id: int) -> HttpResponse:
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    if request.method == 'POST':
        form = HabitForm(request.POST, instance=habit)
        if form.is_valid():
            form.save()
    return redirect('habit_dashboard')


@login_required
@require_POST
def delete_habit(request: HttpRequest, habit_id: int) -> HttpResponse:
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)
    habit.delete()
    return redirect('habit_dashboard')


@login_required
@require_POST
def toggle_habit(request: HttpRequest) -> JsonResponse:
    """習慣の達成状態をトグル（AJAX）。係数の上書きも受け付ける。"""
    try:
        habit_id = int(request.POST.get('habit_id', 0))
        date_str = request.POST.get('date', date.today().isoformat())
        target_date = date.fromisoformat(date_str)

        # 過去7日以内のみ許可
        today = date.today()
        if target_date > today or target_date < today - timedelta(days=6):
            return JsonResponse({'error': 'invalid date'}, status=400)

        habit = get_object_or_404(Habit, id=habit_id, user=request.user)

        # 係数上書き（送られていない場合は None → habit デフォルト）
        coeff_str = request.POST.get('coefficient', '')
        coeff_override: int | None = None
        if coeff_str.isdigit():
            coeff_override = max(1, min(10, int(coeff_str)))

        try:
            record = HabitRecord.objects.get(habit=habit, date=target_date)
            record.delete()
            eff_coeff = habit.coefficient if coeff_override is None else coeff_override
            score_delta = eff_coeff if habit.is_positive else -eff_coeff
            return JsonResponse({'completed': False, 'score_delta': -score_delta})
        except HabitRecord.DoesNotExist:
            HabitRecord.objects.create(habit=habit, date=target_date, coefficient=coeff_override)
            eff_coeff = habit.coefficient if coeff_override is None else coeff_override
            score_delta = eff_coeff if habit.is_positive else -eff_coeff
            return JsonResponse({'completed': True, 'score_delta': score_delta})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def habit_status_json(request: HttpRequest) -> JsonResponse:
    """指定日の習慣状態を返す AJAX エンドポイント。週/年ビューの詳細表示にも使用するため過去全日付に対応。"""
    today = date.today()
    date_str = request.GET.get('date', today.isoformat())
    try:
        target_date = date.fromisoformat(date_str)
        if target_date > today:
            return JsonResponse({'error': 'invalid date'}, status=400)
    except ValueError:
        return JsonResponse({'error': 'invalid date'}, status=400)

    status = selectors.get_today_status(request.user, target_date)
    return JsonResponse({'status': status, 'date': date_str})


@login_required
def habit_list(request: HttpRequest) -> HttpResponse:
    """習慣管理一覧ページ。"""
    habits = selectors.get_habits(request.user)
    return render(request, 'app/habit/list.html', {
        'habits': habits,
        'form': HabitForm(),
    })


@login_required
def habit_heatmap_json(request: HttpRequest) -> JsonResponse:
    """年指定のヒートマップデータを返す AJAX エンドポイント。"""
    today = date.today()
    year_str = request.GET.get('year', '')
    try:
        year = int(year_str)
        data = selectors.get_heatmap_data(request.user, year=year)
    except (ValueError, TypeError):
        data = selectors.get_heatmap_data(request.user, end_date=today)
    return JsonResponse(data)
