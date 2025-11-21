from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from .forms import MemoForm
from .models import Memo


@login_required
def memo_list(request):
    """メモ一覧表示（ページネーション付き）"""
    memo_type_filter = request.GET.get('memo_type', '')
    search_query = request.GET.get('search', '')
    favorite_filter = request.GET.get('favorite', '')
    
    memos = Memo.objects.filter(user=request.user)
    
    if memo_type_filter:
        memos = memos.filter(memo_type=memo_type_filter)
    if search_query:
        memos = memos.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query)
        )
    if favorite_filter == 'true':
        memos = memos.filter(is_favorite=True)
    
    # ページネーション
    paginator = Paginator(memos, 100)  # 100件ずつ表示
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'app/memo/list.html', {
        'page_obj': page_obj,
        'memo_type_filter': memo_type_filter,
        'search_query': search_query,
        'favorite_filter': favorite_filter,
        'memo_type_choices': Memo.MEMO_TYPE_CHOICES,
    })


@login_required
def create_memo(request):
    """メモ新規作成"""
    if request.method == 'POST':
        form = MemoForm(request.POST)
        if form.is_valid():
            memo = form.save(commit=False)
            memo.user = request.user
            memo.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('memo_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = MemoForm()
    
    return render(request, 'app/memo/create_modal.html', {'form': form})


@login_required
def edit_memo(request, memo_id):
    """メモ編集"""
    memo = get_object_or_404(Memo, id=memo_id, user=request.user)
    
    if request.method == 'POST':
        form = MemoForm(request.POST, instance=memo)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('memo_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = MemoForm(instance=memo)
    
    return render(request, 'app/memo/edit_modal.html', {'form': form, 'memo': memo})


@login_required
def delete_memo(request, memo_id):
    """メモ削除"""
    memo = get_object_or_404(Memo, id=memo_id, user=request.user)
    
    if request.method == 'POST':
        memo.delete()
        return redirect('memo_list')
    
    return redirect('memo_list')


@login_required
def toggle_memo_favorite(request, memo_id):
    """メモのお気に入り状態を切り替え（Ajax用）"""
    if request.method == 'POST':
        memo = get_object_or_404(Memo, id=memo_id, user=request.user)
        memo.is_favorite = not memo.is_favorite
        memo.save()
        return JsonResponse({
            'success': True, 
            'is_favorite': memo.is_favorite
        })
    return JsonResponse({'success': False})
