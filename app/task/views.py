import json
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import make_aware

from .forms import TaskForm, TaskLabelForm
from .models import Task, TaskLabel, TempTaskItem
from . import selectors, services


@login_required
def task_list(request: HttpRequest) -> HttpResponse:
    """タスク一覧表示"""
    view_mode = request.GET.get('view_mode', 'month')
    target_date_str = request.GET.get('target_date', None)
    week_start = request.session.get('task_week_start', 'sunday')

    if target_date_str:
        if view_mode == 'day':
            target_date = make_aware(datetime.strptime(target_date_str, '%Y-%m-%d'))
        else:
            target_date = make_aware(datetime.strptime(target_date_str, '%Y-%m'))
    else:
        if view_mode == 'day':
            target_date = make_aware(datetime.now())
        else:
            target_date = make_aware(datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0))
            view_mode = 'month'

    if view_mode == 'day':
        day_start = make_aware(datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0))
        day_end = make_aware(datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59))

        tasks_qs = selectors.get_day_view_tasks(request.user, day_start, day_end)
        tasks_qs = tasks_qs.order_by('start_date', 'priority')

        gantt_data = selectors.build_gantt_data(tasks_qs, day_start, day_end)

        return render(request, 'app/task/list.html', {
            'view_mode': 'day',
            'tasks_count': tasks_qs.count(),
            'gantt_data': gantt_data,
            'target_date': target_date.strftime('%Y-%m-%d'),
            'target_date_display': target_date.strftime('%Y年%m月%d日'),
            'week_start': week_start,
        })

    # 月表示モード
    start_date = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_date = (start_date + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(microseconds=1)

    # カレンダーの前後週（最大7日分）を含むようにタスク取得範囲を拡張
    extended_start = start_date - timedelta(days=7)
    extended_end = end_date + timedelta(days=7)
    month_tasks = selectors.get_month_tasks(request.user, extended_start, extended_end)
    calendar_data, weekday_labels = selectors.build_calendar_data(
        month_tasks, target_date.year, target_date.month, week_start
    )

    return render(request, 'app/task/list.html', {
        'view_mode': 'month',
        'target_month': target_date.strftime('%Y年%m月'),
        'default_target_date': target_date.strftime('%Y-%m'),
        'calendar_data': calendar_data,
        'weekday_labels': weekday_labels,
        'week_start': week_start,
    })


@login_required
def create_task(request: HttpRequest) -> HttpResponse:
    """タスク新規作成"""
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()

            if task.frequency and task.frequency != '':
                services.create_recurring_tasks(task)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('task_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = TaskForm(user=request.user)

    return render(request, 'app/task/create_modal.html', {'form': form})


@login_required
def edit_task(request: HttpRequest, task_id: int) -> HttpResponse:
    """タスク編集"""
    task = get_object_or_404(Task, id=task_id, user=request.user)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            updated_task = form.save()

            if updated_task.frequency and updated_task.frequency != '':
                Task.objects.filter(parent_task=updated_task).delete()
                services.create_recurring_tasks(updated_task)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('task_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = TaskForm(instance=task, user=request.user)

    return render(request, 'app/task/edit_modal.html', {'form': form, 'task': task})


@login_required
def delete_task(request: HttpRequest, task_id: int) -> HttpResponse:
    """タスク削除"""
    task = get_object_or_404(Task, id=task_id, user=request.user)

    if request.method == 'POST':
        task.delete()
        return redirect('task_list')

    return redirect('task_list')


@login_required
def get_day_tasks(request: HttpRequest, date: str) -> JsonResponse:
    """指定日のタスクを取得（API）"""
    try:
        target_date = datetime.strptime(date, '%Y-%m-%d')
        day_start = make_aware(datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0))
        day_end = make_aware(datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59))

        tasks = selectors.get_day_view_tasks(request.user, day_start, day_end).order_by('start_date')
        tasks_data = selectors.build_task_api_json(tasks)

        return JsonResponse({'success': True, 'tasks': tasks_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def temp_task_board(request: HttpRequest) -> HttpResponse:
    """一時タスク管理ボード"""
    return render(request, 'app/task/board.html')


@login_required
def temp_task_api(request: HttpRequest) -> JsonResponse:
    """一時タスク一覧取得・新規作成 API"""
    if request.method == 'GET':
        tasks = TempTaskItem.objects.filter(user=request.user)
        data = [{'id': t.id, 'title': t.title, 'status': t.status, 'order': t.order} for t in tasks]
        return JsonResponse({'tasks': data})

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': '不正なリクエストです'}, status=400)

        title = body.get('title', '').strip()
        status = body.get('status', 'todo')

        if not title:
            return JsonResponse({'error': 'タイトルは必須です'}, status=400)
        if status not in ('todo', 'doing', 'done'):
            return JsonResponse({'error': '不正なステータスです'}, status=400)

        order = TempTaskItem.objects.filter(user=request.user).count()
        task = TempTaskItem.objects.create(user=request.user, title=title, status=status, order=order)
        return JsonResponse({'id': task.id, 'title': task.title, 'status': task.status, 'order': task.order}, status=201)

    return JsonResponse({'error': 'メソッドが許可されていません'}, status=405)


@login_required
def temp_task_detail_api(request: HttpRequest, task_id: int) -> JsonResponse:
    """一時タスク更新・削除 API"""
    task = get_object_or_404(TempTaskItem, id=task_id, user=request.user)

    if request.method == 'PUT':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': '不正なリクエストです'}, status=400)

        if 'title' in body:
            title = body['title'].strip()
            if not title:
                return JsonResponse({'error': 'タイトルは必須です'}, status=400)
            task.title = title

        if 'status' in body:
            status = body['status']
            if status not in ('todo', 'doing', 'done'):
                return JsonResponse({'error': '不正なステータスです'}, status=400)
            task.status = status

        task.save()
        return JsonResponse({'id': task.id, 'title': task.title, 'status': task.status, 'order': task.order})

    if request.method == 'DELETE':
        task.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'error': 'メソッドが許可されていません'}, status=405)


@login_required
def temp_task_clear_api(request: HttpRequest) -> JsonResponse:
    """一時タスク全削除 API"""
    if request.method == 'DELETE':
        TempTaskItem.objects.filter(user=request.user).delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'メソッドが許可されていません'}, status=405)


@login_required
def task_settings(request: HttpRequest) -> HttpResponse:
    """タスク設定画面（ラベル管理・週の開始曜日設定）"""
    labels = selectors.get_labels(request.user)
    current_week_start = request.session.get('task_week_start', 'sunday')

    if request.method == 'POST':
        if 'create_label' in request.POST:
            form = TaskLabelForm(request.POST)
            if form.is_valid():
                label = form.save(commit=False)
                label.user = request.user
                label.save()
                messages.success(request, 'ラベルを作成しました。')
                return redirect('task_settings')

        elif 'edit_label' in request.POST:
            label_id = request.POST.get('label_id')
            label = get_object_or_404(TaskLabel, id=label_id, user=request.user)
            form = TaskLabelForm(request.POST, instance=label)
            if form.is_valid():
                form.save()
                messages.success(request, 'ラベルを更新しました。')
                return redirect('task_settings')

        elif 'delete_label' in request.POST:
            label_id = request.POST.get('label_id')
            label = get_object_or_404(TaskLabel, id=label_id, user=request.user)
            label.delete()
            messages.success(request, 'ラベルを削除しました。')
            return redirect('task_settings')

        elif 'update_week_start' in request.POST:
            selected = request.POST.get('week_start', 'sunday')
            if selected in ['sunday', 'monday']:
                request.session['task_week_start'] = selected
                messages.success(request, '週の開始曜日を更新しました。')
            else:
                messages.error(request, '不正な入力です。')
            return redirect('task_settings')

    return render(request, 'app/task/settings.html', {
        'labels': labels,
        'current_week_start': current_week_start,
    })
