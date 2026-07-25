"""削除済みデータ一覧と復元ビュー。"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .deletion import RestoreError, restore_deleted_item as restore_item
from .models import DeletedItem


@login_required
def trash(request: HttpRequest) -> HttpResponse:
    deleted_items = DeletedItem.objects.filter(user=request.user)[:10]
    return render(request, "app/trash/list.html", {"deleted_items": deleted_items})


@login_required
@require_POST
def restore_deleted_item(request: HttpRequest, deleted_item_id: int) -> HttpResponse:
    deleted_item = get_object_or_404(DeletedItem, pk=deleted_item_id, user=request.user)
    try:
        restored = restore_item(deleted_item, request.user)
    except RestoreError as exc:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": str(exc)}, status=409)
        messages.error(request, str(exc))
        return redirect("trash")

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": True, "id": restored.pk})

    messages.success(request, f"「{deleted_item.object_name}」を元に戻しました。")
    return redirect("trash")


def restore_url(deleted_item: DeletedItem) -> str:
    return reverse("restore_deleted_item", kwargs={"deleted_item_id": deleted_item.pk})
