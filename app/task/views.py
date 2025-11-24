from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils.timezone import make_aware
from django.http import JsonResponse
from .forms import TaskForm, TaskLabelForm
from .models import Task, TaskLabel
from datetime import datetime, timedelta
import calendar


@login_required
def task_list(request):
    """タスク一覧表示"""
    # 表示モードと日付選択
    view_mode = request.GET.get('view_mode', 'month')  # 'month' or 'day'
    target_date_str = request.GET.get('target_date', None)
    week_start = request.session.get('task_week_start', 'sunday')  # 'sunday' or 'monday'
    
    # フィルターパラメータ取得
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    search_query = request.GET.get('search', '')
    
    if target_date_str:
        if view_mode == 'day':
            # 日表示の場合: YYYY-MM-DD形式
            target_date = make_aware(datetime.strptime(target_date_str, '%Y-%m-%d'))
        else:
            # 月表示の場合: YYYY-MM形式
            target_date = make_aware(datetime.strptime(target_date_str, '%Y-%m'))
    else:
        # デフォルト設定
        if view_mode == 'day':
            # 日表示の場合は今日の日付
            target_date = make_aware(datetime.now())
        else:
            # 月表示の場合は現在の月
            target_date = make_aware(datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0))
            view_mode = 'month'
    
    # 日表示モードの場合
    if view_mode == 'day':
        # その日のタスクを取得
        day_start = make_aware(datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0))
        day_end = make_aware(datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59))
        
        tasks = Task.objects.filter(
            user=request.user,
            parent_task__isnull=True
        ).filter(
            Q(start_date__lte=day_end, end_date__gte=day_start) |
            Q(start_date__lte=day_end, end_date__isnull=True) |
            Q(start_date__isnull=True, end_date__gte=day_start)
        ).order_by('start_date', 'priority')
        
        # 検索・フィルター適用
        if status_filter:
            tasks = tasks.filter(status=status_filter)
        if priority_filter:
            tasks = tasks.filter(priority=priority_filter)
        if search_query:
            tasks = tasks.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # ガントチャート用のデータ生成
        gantt_data = []
        for task in tasks:
            # 終日タスクの場合
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
            
            # タスクの開始・終了時刻を取得
            task_start = task.start_date if task.start_date else day_start
            task_end = task.end_date if task.end_date else day_end
            
            # その日の範囲内に制限
            display_start = max(task_start, day_start)
            display_end = min(task_end, day_end)
            
            # 時刻をパーセンテージに変換（0:00 = 0%, 23:59 = 100%）
            start_minutes = display_start.hour * 60 + display_start.minute
            end_minutes = display_end.hour * 60 + display_end.minute
            
            start_percent = (start_minutes / 1440) * 100  # 1440 = 24 * 60
            end_percent = (end_minutes / 1440) * 100
            width_percent = max(end_percent - start_percent, 1)  # 最小1%
            
            gantt_data.append({
                'task': task,
                'start_percent': start_percent,
                'width_percent': width_percent,
                'start_time': display_start.strftime('%H:%M'),
                'end_time': display_end.strftime('%H:%M'),
                'is_all_day': False,
            })
        
        return render(request, 'app/task/list.html', {
            'view_mode': 'day',
            'tasks': tasks,
            'gantt_data': gantt_data,
            'target_date': target_date.strftime('%Y-%m-%d'),
            'target_date_display': target_date.strftime('%Y年%m月%d日'),
            'status_filter': status_filter,
            'priority_filter': priority_filter,
            'search_query': search_query,
            'status_choices': Task.STATUS_CHOICES,
            'priority_choices': Task.PRIORITY_CHOICES,
            'week_start': week_start,
        })
    
    # 月表示モード（既存のコード）
    # 月の開始日と終了日
    start_date = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_date = (start_date + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(microseconds=1)
    
    # 選択された月のタスクを取得（開始日または終了日が選択月内のもの）
    tasks = Task.objects.filter(user=request.user, parent_task__isnull=True)  # 親タスクのみ表示
    
    # 月フィルター（日付が設定されているタスクで、選択月と重なるもの）
    month_tasks = tasks.filter(
        Q(start_date__range=(start_date, end_date)) |
        Q(end_date__range=(start_date, end_date)) |
        Q(start_date__lte=start_date, end_date__gte=end_date)
    )
    
    # 検索・フィルター適用
    filtered_tasks = tasks
    if status_filter:
        filtered_tasks = filtered_tasks.filter(status=status_filter)
    if priority_filter:
        filtered_tasks = filtered_tasks.filter(priority=priority_filter)
    if search_query:
        filtered_tasks = filtered_tasks.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # カレンダー生成
    year = target_date.year
    month = target_date.month
    firstweekday = 6 if week_start == 'sunday' else 0  # Sunday=6, Monday=0
    cal = calendar.Calendar(firstweekday=firstweekday).monthdayscalendar(year, month)
    weekday_labels = ['日', '月', '火', '水', '木', '金', '土'] if week_start == 'sunday' else ['月', '火', '水', '木', '金', '土', '日']
    
    # 各日のタスクを辞書形式で取得（最大5個まで）
    # 複数日にまたがるタスクも各日に表示
    calendar_data = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': 0, 'tasks': []})
            else:
                day_start = make_aware(datetime(year, month, day, 0, 0, 0))
                day_end = make_aware(datetime(year, month, day, 23, 59, 59))
                
                # その日に該当するタスク（開始日〜終了日の範囲内）
                day_tasks = list(month_tasks.filter(
                    Q(start_date__lte=day_end, end_date__gte=day_start) |
                    Q(start_date__lte=day_end, end_date__isnull=True) |
                    Q(start_date__isnull=True, end_date__gte=day_start)
                ).order_by('start_date')[:5])
                
                week_data.append({
                    'day': day,
                    'tasks': day_tasks,
                    'task_count': len(day_tasks)
                })
        calendar_data.append(week_data)
    
    return render(request, 'app/task/list.html', {
        'view_mode': 'month',
        'tasks': filtered_tasks,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'target_month': target_date.strftime('%Y年%m月'),
        'default_target_date': target_date.strftime('%Y-%m'),
        'calendar_data': calendar_data,
        'weekday_labels': weekday_labels,
        'week_start': week_start,
    })


@login_required
def create_task(request):
    """タスク新規作成"""
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            
            # 繰り返しタスクの場合、子タスクを自動生成
            if task.frequency and task.frequency != '':
                create_recurring_tasks(task)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('task_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = TaskForm(user=request.user)
    
    return render(request, 'app/task/create_modal.html', {'form': form})


def create_recurring_tasks(parent_task):
    """繰り返しタスクの子タスクを作成"""
    from dateutil.relativedelta import relativedelta
    
    if not parent_task.start_date:
        return
    
    frequency = parent_task.frequency
    interval = parent_task.repeat_interval or 1
    count = parent_task.repeat_count
    
    # 繰り返し回数が指定されていない、または無効な場合はスキップ
    if not count or count <= 0:
        return
    
    current_start = parent_task.start_date
    current_end = parent_task.end_date
    
    for i in range(count):
        # 次の繰り返し日を計算
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
        
        # 子タスクを作成
        Task.objects.create(
            user=parent_task.user,
            title=parent_task.title,
            frequency='',  # 子タスクは繰り返しなし
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


@login_required
def edit_task(request, task_id):
    """タスク編集"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            updated_task = form.save()
            
            # 繰り返しタスクの設定が変更された場合、既存の子タスクを削除して再作成
            if updated_task.frequency and updated_task.frequency != '':
                # 既存の子タスクを削除
                Task.objects.filter(parent_task=updated_task).delete()
                # 新しい子タスクを作成
                create_recurring_tasks(updated_task)
            
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
def delete_task(request, task_id):
    """タスク削除"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        task.delete()
        return redirect('task_list')
    
    return redirect('task_list')


@login_required
def get_day_tasks(request, date):
    """指定日のタスクを取得（API）"""
    try:
        # 日付をパース
        target_date = datetime.strptime(date, '%Y-%m-%d')
        day_start = make_aware(datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0))
        day_end = make_aware(datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59))
        
        # その日のタスクを取得（開始日〜終了日の範囲内、または親タスクのみ）
        tasks = Task.objects.filter(
            user=request.user,
            parent_task__isnull=True  # 親タスクのみ
        ).filter(
            Q(start_date__lte=day_end, end_date__gte=day_start) |
            Q(start_date__lte=day_end, end_date__isnull=True) |
            Q(start_date__isnull=True, end_date__gte=day_start)
        ).order_by('start_date')
        
        # JSON形式で返す
        tasks_data = []
        for task in tasks:
            # 日付表示用のフォーマット
            if task.all_day:
                date_display = f"{task.start_date.strftime('%Y-%m-%d')}" if task.start_date else ''
                if task.end_date and task.start_date.date() != task.end_date.date():
                    date_display += f" 〜 {task.end_date.strftime('%Y-%m-%d')}"
            else:
                date_display = f"{task.start_date.strftime('%Y-%m-%d %H:%M')}" if task.start_date else ''
                if task.end_date:
                    if task.start_date.date() == task.end_date.date():
                        date_display += f" 〜 {task.end_date.strftime('%H:%M')}"
                    else:
                        date_display += f" 〜 {task.end_date.strftime('%Y-%m-%d %H:%M')}"
            
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
                    'color': task.label.color
                } if task.label else None,
            })
        
        return JsonResponse({'success': True, 'tasks': tasks_data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def task_settings(request):
    """タスク設定画面（ラベル管理・週の開始曜日設定）"""
    labels = TaskLabel.objects.filter(user=request.user)
    current_week_start = request.session.get('task_week_start', 'sunday')
    
    # ラベル作成
    if request.method == 'POST':
        if 'create_label' in request.POST:
            form = TaskLabelForm(request.POST)
            if form.is_valid():
                label = form.save(commit=False)
                label.user = request.user
                label.save()
                messages.success(request, 'ラベルを作成しました。')
                return redirect('task_settings')
        
        # ラベル編集
        elif 'edit_label' in request.POST:
            label_id = request.POST.get('label_id')
            label = get_object_or_404(TaskLabel, id=label_id, user=request.user)
            form = TaskLabelForm(request.POST, instance=label)
            if form.is_valid():
                form.save()
                messages.success(request, 'ラベルを更新しました。')
                return redirect('task_settings')
        
        # ラベル削除
        elif 'delete_label' in request.POST:
            label_id = request.POST.get('label_id')
            label = get_object_or_404(TaskLabel, id=label_id, user=request.user)
            label.delete()
            messages.success(request, 'ラベルを削除しました。')
            return redirect('task_settings')
        
        # 週の開始曜日設定
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
