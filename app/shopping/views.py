from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ShoppingItemForm
from .models import ShoppingItem
from . import selectors, services


@login_required
def shopping_list(request):
    """買うものリスト一覧表示"""
    search_query = request.GET.get('search', '')
    shopping_items = selectors.get_shopping_items(request.user, search_query)

    return render(request, 'app/shopping/list.html', {
        'one_time_items': selectors.get_one_time_items(shopping_items),
        'recurring_items': selectors.get_recurring_items(shopping_items),
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
        field_type = request.POST.get('field_type', '')
        action = request.POST.get('action', '')
        services.update_item_count(shopping_item, field_type, action)
        return JsonResponse({
            'success': True,
            'remaining_count': shopping_item.remaining_count,
            'threshold_count': shopping_item.threshold_count,
            'status': shopping_item.get_status_display(),
            'status_code': shopping_item.status,
        })

    return JsonResponse({'success': False})
