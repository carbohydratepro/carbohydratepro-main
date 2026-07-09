"""一括削除の共通ヘルパー。

各一覧画面の「選択モード → まとめて削除」から呼ばれる。
POST の JSON ボディ {"ids": [1, 2, 3]} を受け取り、ログインユーザーが所有する
対象だけを削除して件数を返す。
"""
from __future__ import annotations

import json
from typing import Type

from django.db.models import Model
from django.http import HttpRequest, JsonResponse


def bulk_delete_response(request: HttpRequest, model: Type[Model]) -> JsonResponse:
    """指定モデルの複数レコードを、所有者チェック付きで一括削除する。"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'method_not_allowed'}, status=405)

    try:
        payload = json.loads(request.body or '{}')
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'invalid_json'}, status=400)

    raw_ids = payload.get('ids', [])
    if not isinstance(raw_ids, list):
        return JsonResponse({'success': False, 'error': 'invalid_ids'}, status=400)

    ids = [int(i) for i in raw_ids if isinstance(i, int) or (isinstance(i, str) and i.isdigit())]
    if not ids:
        return JsonResponse({'success': True, 'deleted': 0})

    queryset = model.objects.filter(user=request.user, id__in=ids)
    deleted_count = queryset.count()
    queryset.delete()
    return JsonResponse({'success': True, 'deleted': deleted_count})
