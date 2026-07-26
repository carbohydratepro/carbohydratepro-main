from __future__ import annotations

from typing import Any

from django.db.models import Count, Max, Q, QuerySet, Sum
from django.db.models.functions import Coalesce

from .models import CookingDish

SORT_OPTIONS = {
    "recent": ("-is_favorite", "-updated_at", "-pk"),
    "last_cooked": ("-last_cooked_on", "-updated_at", "-pk"),
    "count": ("-cooked_count", "-updated_at", "-pk"),
    "name": ("title", "pk"),
}


def get_cooking_dishes(user: Any, search: str = "", sort: str = "recent") -> QuerySet[CookingDish]:
    dishes = CookingDish.objects.filter(user=user).annotate(
        cooked_count=Coalesce(Sum("histories__count"), 0),
        last_cooked_on=Max("histories__cooked_on"),
        history_days=Count("histories", distinct=True),
    )
    if search:
        dishes = dishes.filter(Q(title__icontains=search) | Q(ingredients__icontains=search))
    return dishes.order_by(*SORT_OPTIONS.get(sort, SORT_OPTIONS["recent"]))
