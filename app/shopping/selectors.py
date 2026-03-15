from __future__ import annotations

from typing import TYPE_CHECKING

from django.db.models import Q, QuerySet

from .models import ShoppingItem

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser


def get_shopping_items(user: AbstractBaseUser, search_query: str = '') -> QuerySet:
    """買うものリスト一覧を取得"""
    items = ShoppingItem.objects.filter(user=user)
    if search_query:
        items = items.filter(
            Q(title__icontains=search_query) |
            Q(memo__icontains=search_query)
        )
    return items


def get_one_time_items(shopping_items: QuerySet) -> QuerySet:
    """一回限りの買うものを取得（未チェックを先に）"""
    return shopping_items.filter(frequency='one_time').order_by('is_checked', 'created_date')


def get_recurring_items(shopping_items: QuerySet) -> QuerySet:
    """定期的な買うものを取得（不足を先に）"""
    return shopping_items.filter(frequency='recurring').order_by('-status', 'remaining_count', '-updated_date')
