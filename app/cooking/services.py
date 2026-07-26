from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Any

from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import transaction

from .models import CookingDish, CookingHistory


def get_image_names(dish: CookingDish) -> set[str]:
    names = {photo.name for photo in dish.photos if getattr(photo, "name", "")}
    for step in dish.steps.all():
        names.update(photo.name for photo in step.photos if getattr(photo, "name", ""))
    return names


def _delete_files(file_names: Iterable[str]) -> None:
    for file_name in file_names:
        if file_name.startswith("cooking/"):
            default_storage.delete(file_name)


def save_cooking_dish(
    dish_form: Any,
    step_formset: Any,
    user: Any,
    *,
    previous_file_names: set[str] | None = None,
) -> CookingDish:
    """料理と並び順を正規化した手順を一括保存する。"""
    with transaction.atomic():
        dish = dish_form.save(commit=False)
        dish.user = user
        dish.save()

        active_forms = []
        for form in step_formset.forms:
            cleaned_data = getattr(form, "cleaned_data", {})
            if not cleaned_data:
                continue
            if cleaned_data.get("DELETE"):
                if form.instance.pk:
                    form.instance.delete()
                continue
            instruction = str(cleaned_data.get("instruction") or "").strip()
            if not instruction:
                continue
            active_forms.append(form)

        active_forms.sort(key=lambda form: int(form.cleaned_data.get("position") or 1))
        for position, form in enumerate(active_forms, start=1):
            instruction = str(form.cleaned_data.get("instruction") or "").strip()
            step = form.save(commit=False)
            step.dish = dish
            step.position = position
            step.instruction = instruction
            step.save()

        current_file_names = get_image_names(dish)
        stale_file_names = (previous_file_names or set()) - current_file_names
        if stale_file_names:
            transaction.on_commit(lambda: _delete_files(stale_file_names))

    return dish


def record_cooked_today(dish: CookingDish, today: date) -> CookingHistory:
    """今日の作成回数を競合に耐える形で1増やす。"""
    with transaction.atomic():
        locked_dish = CookingDish.objects.select_for_update().get(pk=dish.pk, user=dish.user)
        history, created = CookingHistory.objects.get_or_create(
            dish=locked_dish,
            cooked_on=today,
            defaults={"count": 1},
        )
        if not created:
            if history.count >= 999:
                raise ValidationError("1日に記録できる回数は999回までです。")
            history.count += 1
            history.save(update_fields=["count", "updated_at"])
    return history
