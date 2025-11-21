from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from .forms import ShoppingItemForm
from .models import ShoppingItem


@login_required
def shopping_list(request):
    """買うものリスト一覧表示"""
    search_query = request.GET.get('search', '')
    
    shopping_items = ShoppingItem.objects.filter(user=request.user)
    
    if search_query:
        shopping_items = shopping_items.filter(
            Q(title__icontains=search_query) | 
            Q(memo__icontains=search_query)
        )
    
    # 頻度別に分けて取得（不足を上位に、その後残数が少ない順）
    one_time_items = shopping_items.filter(frequency='one_time').order_by('status', 'remaining_count', '-updated_date')
    recurring_items = shopping_items.filter(frequency='recurring').order_by('status', 'remaining_count', '-updated_date')
    
    return render(request, 'app/shopping/list.html', {
        'one_time_items': one_time_items,
        'recurring_items': recurring_items,
        'search_query': search_query,
        'total_count': shopping_items.count(),
    })


@login_required
def create_shopping_item(request):
    """買うものリスト新規作成"""
    if request.method == 'POST':
        form = ShoppingItemForm(request.POST)
        if form.is_valid():
            shopping_item = form.save(commit=False)
            shopping_item.user = request.user
            shopping_item.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('shopping_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = ShoppingItemForm()
    
    return render(request, 'app/shopping/create_modal.html', {'form': form})


@login_required
def edit_shopping_item(request, item_id):
    """買うものリスト編集"""
    shopping_item = get_object_or_404(ShoppingItem, id=item_id, user=request.user)
    
    if request.method == 'POST':
        form = ShoppingItemForm(request.POST, instance=shopping_item)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('shopping_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = ShoppingItemForm(instance=shopping_item)
    
    return render(request, 'app/shopping/edit_modal.html', {'form': form, 'shopping_item': shopping_item})


@login_required
def delete_shopping_item(request, item_id):
    """買うものリスト削除"""
    shopping_item = get_object_or_404(ShoppingItem, id=item_id, user=request.user)
    
    if request.method == 'POST':
        shopping_item.delete()
        return redirect('shopping_list')
    
    return redirect('shopping_list')


@login_required
def update_shopping_count(request, item_id):
    """残数・不足数の更新（Ajax用）"""
    if request.method == 'POST':
        shopping_item = get_object_or_404(ShoppingItem, id=item_id, user=request.user)
        field_type = request.POST.get('field_type')  # 'remaining' or 'threshold'
        action = request.POST.get('action')
        
        # どのフィールドを更新するか判定
        if field_type == 'remaining':
            if action == 'increase':
                shopping_item.remaining_count = min(999, shopping_item.remaining_count + 1)
            elif action == 'increase10':
                shopping_item.remaining_count = min(999, shopping_item.remaining_count + 10)
            elif action == 'decrease':
                # 0未満にならないように制限
                if shopping_item.remaining_count > 0:
                    shopping_item.remaining_count -= 1
            elif action == 'decrease10':
                # 0未満にならないように制限
                shopping_item.remaining_count = max(0, shopping_item.remaining_count - 10)
        elif field_type == 'threshold':
            if action == 'increase':
                shopping_item.threshold_count = min(999, shopping_item.threshold_count + 1)
            elif action == 'increase10':
                shopping_item.threshold_count = min(999, shopping_item.threshold_count + 10)
            elif action == 'decrease':
                # 0未満にならないように制限
                if shopping_item.threshold_count > 0:
                    shopping_item.threshold_count -= 1
            elif action == 'decrease10':
                # 0未満にならないように制限
                shopping_item.threshold_count = max(0, shopping_item.threshold_count - 10)
        
        shopping_item.save()  # save()メソッドでステータスも自動更新される
        
        return JsonResponse({
            'success': True,
            'remaining_count': shopping_item.remaining_count,
            'threshold_count': shopping_item.threshold_count,
            'status': shopping_item.get_status_display(),
            'status_code': shopping_item.status
        })
    
    return JsonResponse({'success': False})
