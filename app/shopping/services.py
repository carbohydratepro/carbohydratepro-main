from __future__ import annotations

from .models import ShoppingItem


def update_item_count(shopping_item: ShoppingItem, field_type: str, action: str) -> None:
    """残数・不足数を更新して保存"""
    if field_type == 'remaining':
        if action == 'increase':
            shopping_item.remaining_count = min(999, shopping_item.remaining_count + 1)
        elif action == 'increase10':
            shopping_item.remaining_count = min(999, shopping_item.remaining_count + 10)
        elif action == 'decrease':
            if shopping_item.remaining_count > 0:
                shopping_item.remaining_count -= 1
        elif action == 'decrease10':
            shopping_item.remaining_count = max(0, shopping_item.remaining_count - 10)
    elif field_type == 'threshold':
        if action == 'increase':
            shopping_item.threshold_count = min(999, shopping_item.threshold_count + 1)
        elif action == 'increase10':
            shopping_item.threshold_count = min(999, shopping_item.threshold_count + 10)
        elif action == 'decrease':
            if shopping_item.threshold_count > 0:
                shopping_item.threshold_count -= 1
        elif action == 'decrease10':
            shopping_item.threshold_count = max(0, shopping_item.threshold_count - 10)
    shopping_item.save()
