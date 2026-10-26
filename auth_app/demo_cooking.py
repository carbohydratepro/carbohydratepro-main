"""料理デモ。DBやユーザーの写真を参照しない閲覧用データ。"""
from datetime import date
from types import SimpleNamespace

from django.core.paginator import Paginator
from django.http import QueryDict


def get_cooking_context(params: QueryDict) -> dict[str, object]:
    dishes = [
        SimpleNamespace(
            id=1, title='チキンカレー', ingredients='鶏肉、玉ねぎ、にんじん、カレールー',
            cooked_count=5, last_cooked_on=date(2026, 3, 25), is_favorite=True, cover_photo=None,
        ),
        SimpleNamespace(
            id=2, title='鮭のホイル焼き', ingredients='鮭、きのこ、玉ねぎ、バター',
            cooked_count=3, last_cooked_on=date(2026, 3, 20), is_favorite=False, cover_photo=None,
        ),
        SimpleNamespace(
            id=3, title='トマトパスタ', ingredients='トマト、パスタ、にんにく、オリーブオイル',
            cooked_count=8, last_cooked_on=date(2026, 3, 23), is_favorite=True, cover_photo=None,
        ),
    ]
    search = params.get('search', '').strip()
    sort = params.get('sort', 'recent')
    if sort not in ('recent', 'last_cooked', 'count', 'name'):
        sort = 'recent'
    if search:
        dishes = [
            dish for dish in dishes
            if search.casefold() in (dish.title + dish.ingredients).casefold()
        ]
    if sort == 'name':
        dishes.sort(key=lambda dish: dish.title)
    elif sort == 'count':
        dishes.sort(key=lambda dish: dish.cooked_count, reverse=True)
    elif sort == 'last_cooked':
        dishes.sort(key=lambda dish: dish.last_cooked_on, reverse=True)
    return {
        'is_demo': True,
        'page_obj': Paginator(dishes, 12).get_page(params.get('page')),
        'search_query': search,
        'sort': sort,
    }
