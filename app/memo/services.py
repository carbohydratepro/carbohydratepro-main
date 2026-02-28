from __future__ import annotations

from .models import MemoType


def ensure_default_memo_types() -> None:
    """デフォルトメモ種別（共有）が存在することを保証"""
    defaults = [
        ('メモ', '#007bff'),
        ('アイデア', '#28a745'),
        ('その他', '#6c757d'),
    ]
    for name, color in defaults:
        MemoType.objects.get_or_create(user=None, name=name, defaults={'color': color})
