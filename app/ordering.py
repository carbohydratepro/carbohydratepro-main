"""ユーザー所有の設定項目に共通する表示順操作。"""

from __future__ import annotations

from typing import Any

from django.db import models, transaction
from django.db.models import Max


def next_sort_order(model: type[models.Model], user: Any) -> int:
    """ユーザーの末尾へ追加するための表示順を返す。"""
    maximum = model._base_manager.filter(user=user).aggregate(value=Max("sort_order"))["value"]
    return int(maximum if maximum is not None else -1) + 1


def move_owned_item(
    model: type[models.Model],
    user: Any,
    item_id: Any,
    direction: str,
) -> bool:
    """所有者の並びの中だけで項目を1つ上下へ移動する。"""
    if direction not in {"up", "down"}:
        return False

    with transaction.atomic():
        items = list(
            model._base_manager.select_for_update()
            .filter(user=user)
            .order_by("sort_order", "pk")
        )
        for position, item in enumerate(items):
            if item.sort_order != position:
                model._base_manager.filter(pk=item.pk, user=user).update(sort_order=position)
                item.sort_order = position

        current_index = next(
            (index for index, item in enumerate(items) if str(item.pk) == str(item_id)),
            None,
        )
        if current_index is None:
            return False
        target_index = current_index - 1 if direction == "up" else current_index + 1
        if target_index < 0 or target_index >= len(items):
            return False

        current = items[current_index]
        target = items[target_index]
        current.sort_order, target.sort_order = target.sort_order, current.sort_order
        model._base_manager.filter(pk=current.pk, user=user).update(sort_order=current.sort_order)
        model._base_manager.filter(pk=target.pk, user=user).update(sort_order=target.sort_order)
    return True
