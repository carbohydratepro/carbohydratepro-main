from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Q, QuerySet

from .models import Memo, MemoType

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser


def get_memo_types(user: AbstractBaseUser) -> QuerySet:
    """ユーザーのメモ種別一覧を取得（共有種別含む）"""
    return MemoType.objects.filter(
        Q(user=user) | Q(user__isnull=True)
    ).order_by('name')


def get_memos(
    user: AbstractBaseUser,
    memo_type_filter: str = '',
    search_query: str = '',
    favorite_filter: str = '',
) -> QuerySet:
    """フィルター適用済みメモクエリセットを取得"""
    memos = Memo.objects.filter(user=user).select_related('memo_type')
    if memo_type_filter:
        memos = memos.filter(memo_type_id=memo_type_filter)
    if search_query:
        memos = memos.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    if favorite_filter == 'true':
        memos = memos.filter(is_favorite=True)
    return memos
