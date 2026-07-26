from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import selectors, services
from .forms import CookingDishForm, CookingHistoryForm, CookingStepFormSet
from .models import CookingDish, CookingHistory


def _detail_context(
    dish: CookingDish,
    history_form: CookingHistoryForm | None = None,
) -> dict[str, Any]:
    histories = dish.histories.all()
    total_count = histories.aggregate(total=Sum("count"))["total"] or 0
    return {
        "dish": dish,
        "steps": dish.steps.all(),
        "histories": histories,
        "total_count": total_count,
        "last_cooked_on": histories.first().cooked_on if histories.exists() else None,
        "history_form": history_form
        or CookingHistoryForm(initial={"cooked_on": timezone.localdate(), "count": 1}),
    }


@login_required
def cooking_list(request: HttpRequest) -> HttpResponse:
    search = request.GET.get("search", "").strip()
    sort = request.GET.get("sort", "recent")
    if sort not in selectors.SORT_OPTIONS:
        sort = "recent"
    dishes = selectors.get_cooking_dishes(request.user, search, sort)
    page_obj = Paginator(dishes, 12).get_page(request.GET.get("page"))
    return render(
        request,
        "app/cooking/list.html",
        {"page_obj": page_obj, "search_query": search, "sort": sort},
    )


@login_required
def cooking_detail(request: HttpRequest, dish_id: int) -> HttpResponse:
    dish = get_object_or_404(CookingDish, pk=dish_id, user=request.user)
    return render(request, "app/cooking/detail.html", _detail_context(dish))


def _dish_form_response(
    request: HttpRequest,
    dish: CookingDish,
    *,
    is_create: bool,
) -> HttpResponse:
    previous_file_names = set() if is_create else services.get_image_names(dish)
    if request.method == "POST":
        form = CookingDishForm(request.POST, request.FILES, instance=dish)
        step_formset = CookingStepFormSet(
            request.POST,
            request.FILES,
            instance=dish,
            prefix="steps",
        )
        form_is_valid = form.is_valid()
        steps_are_valid = step_formset.is_valid()
        if form_is_valid and steps_are_valid:
            saved_dish = services.save_cooking_dish(
                form,
                step_formset,
                request.user,
                previous_file_names=previous_file_names,
            )
            messages.success(
                request, "料理を登録しました。" if is_create else "料理を更新しました。"
            )
            return redirect("cooking_detail", dish_id=saved_dish.pk)
    else:
        form = CookingDishForm(instance=dish)
        step_formset = CookingStepFormSet(instance=dish, prefix="steps")

    return render(
        request,
        "app/cooking/form.html",
        {"form": form, "step_formset": step_formset, "dish": dish, "is_create": is_create},
    )


@login_required
def cooking_create(request: HttpRequest) -> HttpResponse:
    return _dish_form_response(request, CookingDish(user=request.user), is_create=True)


@login_required
def cooking_edit(request: HttpRequest, dish_id: int) -> HttpResponse:
    dish = get_object_or_404(CookingDish, pk=dish_id, user=request.user)
    return _dish_form_response(request, dish, is_create=False)


@login_required
@require_POST
def cooking_delete(request: HttpRequest, dish_id: int) -> HttpResponse:
    from app.deletion import archive_and_delete

    dish = get_object_or_404(CookingDish, pk=dish_id, user=request.user)
    archive_and_delete(dish, request.user)
    messages.success(request, "料理を削除しました。ごみ箱から元に戻せます。")
    return redirect("cooking_list")


@login_required
@require_POST
def cooking_record_today(request: HttpRequest, dish_id: int) -> HttpResponse:
    dish = get_object_or_404(CookingDish, pk=dish_id, user=request.user)
    try:
        services.record_cooked_today(dish, timezone.localdate())
    except ValidationError as exc:
        messages.error(request, exc.message)
    else:
        messages.success(request, "今日作った回数を記録しました。")
    return redirect("cooking_detail", dish_id=dish.pk)


@login_required
@require_POST
def cooking_history_add(request: HttpRequest, dish_id: int) -> HttpResponse:
    dish = get_object_or_404(CookingDish, pk=dish_id, user=request.user)
    form = CookingHistoryForm(request.POST, instance=CookingHistory(dish=dish))
    if form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error(
                "cooked_on", "この日付の記録は既にあります。既存の行を編集してください。"
            )
        else:
            messages.success(request, "作成履歴を追加しました。")
            return redirect("cooking_detail", dish_id=dish.pk)
    return render(request, "app/cooking/detail.html", _detail_context(dish, form))


@login_required
@require_POST
def cooking_history_update(request: HttpRequest, dish_id: int, history_id: int) -> HttpResponse:
    dish = get_object_or_404(CookingDish, pk=dish_id, user=request.user)
    history = get_object_or_404(CookingHistory, pk=history_id, dish=dish)
    form = CookingHistoryForm(request.POST, instance=history)
    if form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            messages.error(request, "この日付の記録は既にあります。")
        else:
            messages.success(request, "作成履歴を更新しました。")
    else:
        messages.error(request, "作成履歴を更新できませんでした。日付と回数を確認してください。")
    return redirect("cooking_detail", dish_id=dish.pk)


@login_required
@require_POST
def cooking_history_delete(request: HttpRequest, dish_id: int, history_id: int) -> HttpResponse:
    dish = get_object_or_404(CookingDish, pk=dish_id, user=request.user)
    history = get_object_or_404(CookingHistory, pk=history_id, dish=dish)
    history.delete()
    messages.success(request, "作成履歴を削除しました。")
    return redirect("cooking_detail", dish_id=dish.pk)
