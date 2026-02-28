from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MemoForm, MemoTypeForm
from .models import Memo, MemoType
from . import selectors, services


@login_required
def memo_list(request: HttpRequest) -> HttpResponse:
    """メモ一覧表示（ページネーション付き）"""
    services.ensure_default_memo_types()
    memo_type_filter = request.GET.get('memo_type', '')
    search_query = request.GET.get('search', '')
    favorite_filter = request.GET.get('favorite', '')
    per_page_raw = request.GET.get('per_page', '20')
    per_page_options = ['10', '20', '50', '100']
    per_page = int(per_page_raw) if per_page_raw in per_page_options else 20

    memos = selectors.get_memos(request.user, memo_type_filter, search_query, favorite_filter)
    paginator = Paginator(memos, per_page)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'app/memo/list.html', {
        'page_obj': page_obj,
        'memo_type_filter': memo_type_filter,
        'search_query': search_query,
        'favorite_filter': favorite_filter,
        'memo_type_choices': selectors.get_memo_types(request.user),
        'per_page': per_page,
        'per_page_options': per_page_options,
    })


@login_required
def create_memo(request: HttpRequest) -> HttpResponse:
    """メモ新規作成"""
    services.ensure_default_memo_types()
    if request.method == 'POST':
        form = MemoForm(request.POST, user=request.user)
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
        form = MemoForm(user=request.user)

    return render(request, 'app/memo/create_modal.html', {'form': form})


@login_required
def edit_memo(request: HttpRequest, memo_id: int) -> HttpResponse:
    """メモ編集"""
    memo = get_object_or_404(Memo, id=memo_id, user=request.user)
    services.ensure_default_memo_types()

    if request.method == 'POST':
        form = MemoForm(request.POST, instance=memo, user=request.user)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('memo_list')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = MemoForm(instance=memo, user=request.user)

    return render(request, 'app/memo/edit_modal.html', {'form': form, 'memo': memo})


@login_required
def delete_memo(request: HttpRequest, memo_id: int) -> HttpResponse:
    """メモ削除"""
    memo = get_object_or_404(Memo, id=memo_id, user=request.user)

    if request.method == 'POST':
        memo.delete()
        return redirect('memo_list')

    return redirect('memo_list')


@login_required
def toggle_memo_favorite(request: HttpRequest, memo_id: int) -> JsonResponse:
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


@login_required
def memo_settings(request: HttpRequest) -> HttpResponse:
    services.ensure_default_memo_types()
    memo_types = selectors.get_memo_types(request.user).order_by('user', 'name')
    if request.method == 'POST':
        # 作成
        if 'create_memo_type' in request.POST:
            count = MemoType.objects.filter(user=request.user).count()
            if count >= 100:
                messages.error(request, 'これ以上種別を追加できません（最大100件）。')
                return redirect('memo_settings')
            form = MemoTypeForm(request.POST)
            if form.is_valid():
                memo_type = form.save(commit=False)
                memo_type.user = request.user
                memo_type.save()
                messages.success(request, '種別を追加しました。')
            else:
                messages.error(request, '種別の作成に失敗しました。')
            return redirect('memo_settings')
        # 編集
        if 'edit_memo_type' in request.POST:
            memo_type_id = request.POST.get('memo_type_id')
            memo_type = get_object_or_404(MemoType, id=memo_type_id)
            if memo_type.user and memo_type.user != request.user:
                messages.error(request, '編集権限がありません。')
                return redirect('memo_settings')
            if not memo_type.user and memo_type.name == 'その他':
                messages.error(request, '「その他」は変更できません。')
                return redirect('memo_settings')
            form = MemoTypeForm(request.POST, instance=memo_type)
            if form.is_valid():
                form.save()
                messages.success(request, '種別を更新しました。')
            else:
                messages.error(request, '種別の更新に失敗しました。')
            return redirect('memo_settings')
        # 削除
        if 'delete_memo_type' in request.POST:
            memo_type_id = request.POST.get('memo_type_id')
            memo_type = get_object_or_404(MemoType, id=memo_type_id)
            if memo_type.user and memo_type.user != request.user:
                messages.error(request, '削除権限がありません。')
                return redirect('memo_settings')
            if not memo_type.user and memo_type.name == 'その他':
                messages.error(request, '「その他」は削除できません。')
                return redirect('memo_settings')
            if memo_type.memos.exists():
                messages.error(request, 'この種別を利用しているメモがあるため削除できません。')
            else:
                memo_type.delete()
                messages.success(request, '種別を削除しました。')
            return redirect('memo_settings')

    return render(request, 'app/memo/settings.html', {
        'memo_types': memo_types,
        'form': MemoTypeForm(),
    })
