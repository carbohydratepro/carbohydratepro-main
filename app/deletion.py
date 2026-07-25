"""ユーザー所有データの削除履歴作成と復元。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from django.contrib.auth import get_user_model
from django.db import IntegrityError, models, transaction

from .expenses.models import RecurringPayment, Transaction
from .habit.models import Habit, HabitRecord
from .memo.models import Memo
from .models import DeletedItem
from .shopping.models import ShoppingItem
from .task.models import Task, TempTaskItem, TempTaskSet

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser
    from django.db.models import Model, QuerySet


TRASH_LIMIT = 10
SNAPSHOT_VERSION = 1


class RestoreError(Exception):
    """削除履歴を安全に復元できない場合のエラー。"""


@dataclass(frozen=True)
class DeletionSpec:
    key: str
    label: str
    model: type[models.Model]
    name: Callable[[models.Model], str]


def _transaction_name(instance: models.Model) -> str:
    transaction_item = instance
    purpose = str(getattr(transaction_item, "purpose", "")).strip()
    amount = getattr(transaction_item, "amount", "")
    return purpose or f"{amount}円"


def _title_name(instance: models.Model) -> str:
    return str(getattr(instance, "title", ""))


def _purpose_name(instance: models.Model) -> str:
    return str(getattr(instance, "purpose", ""))


def _set_name(instance: models.Model) -> str:
    return str(getattr(instance, "name", ""))


DELETION_SPECS = (
    DeletionSpec("transaction", "家計簿", Transaction, _transaction_name),
    DeletionSpec("recurring_payment", "定期支払い", RecurringPayment, _purpose_name),
    DeletionSpec("task", "予定", Task, _title_name),
    DeletionSpec("temp_task", "一時タスク", TempTaskItem, _title_name),
    DeletionSpec("temp_task_set", "一時タスクセット", TempTaskSet, _set_name),
    DeletionSpec("memo", "メモ", Memo, _title_name),
    DeletionSpec("shopping_item", "買いもの", ShoppingItem, _title_name),
    DeletionSpec("habit", "習慣", Habit, _title_name),
)

_SPECS_BY_MODEL = {spec.model: spec for spec in DELETION_SPECS}
_SPECS_BY_KEY = {spec.key: spec for spec in DELETION_SPECS}


def _snapshot_instance(
    instance: models.Model,
    *,
    excluded_fields: set[str] | None = None,
) -> dict[str, Any]:
    excluded = excluded_fields or set()
    fields: dict[str, Any] = {}
    for field in instance._meta.concrete_fields:
        if field.primary_key or field.name == "user" or field.name in excluded:
            continue
        fields[field.attname] = getattr(instance, field.attname)
    return {"pk": instance.pk, "fields": fields}


def _build_payload(instance: models.Model) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "version": SNAPSHOT_VERSION,
        "object": _snapshot_instance(instance),
        "relations": {},
    }

    if isinstance(instance, Habit):
        payload["relations"]["records"] = [
            _snapshot_instance(record, excluded_fields={"habit"})
            for record in instance.records.order_by("pk")
        ]
    elif isinstance(instance, Task):
        payload["relations"]["recurring_instances"] = [
            _snapshot_instance(child, excluded_fields={"parent_task"})
            for child in instance.recurring_instances.order_by("pk")
        ]
    elif isinstance(instance, TempTaskSet):
        payload["relations"]["items"] = [
            _snapshot_instance(item, excluded_fields={"task_set"})
            for item in instance.items.order_by("pk")
        ]

    return payload


def _trim_history(user: AbstractBaseUser) -> None:
    stale_ids = list(
        DeletedItem.objects.filter(user=user)
        .order_by("-deleted_at", "-pk")
        .values_list("pk", flat=True)[TRASH_LIMIT:]
    )
    if stale_ids:
        DeletedItem.objects.filter(pk__in=stale_ids, user=user).delete()


def _create_history(instance: models.Model, user: AbstractBaseUser) -> DeletedItem:
    spec = _SPECS_BY_MODEL.get(type(instance))
    if spec is None:
        raise ValueError(f"削除履歴に対応していないモデルです: {type(instance).__name__}")
    if getattr(instance, "user_id", None) != user.pk:
        raise ValueError("他のユーザーのデータは削除履歴へ保存できません")

    return DeletedItem.objects.create(
        user=user,
        object_type=spec.key,
        object_label=spec.label,
        object_name=spec.name(instance)[:200],
        payload=_build_payload(instance),
    )


def archive_and_delete(instance: models.Model, user: AbstractBaseUser) -> DeletedItem:
    """1件を削除履歴へ保存してから削除する。"""
    user_model = get_user_model()
    with transaction.atomic():
        user_model.objects.select_for_update().get(pk=user.pk)
        deleted_item = _create_history(instance, user)
        instance.delete()
        _trim_history(user)
    return deleted_item


def archive_and_delete_queryset(
    queryset: QuerySet[Model],
    user: AbstractBaseUser,
) -> int:
    """QuerySetを削除し、復元対象として新しい順に最大10件を保存する。"""
    deleted_count = queryset.count()
    if deleted_count == 0:
        return 0

    # 一括削除の中ではPKが大きいものを新しいデータとして残す。
    instances = list(queryset.order_by("-pk")[:TRASH_LIMIT])
    user_model = get_user_model()
    with transaction.atomic():
        user_model.objects.select_for_update().get(pk=user.pk)
        for instance in reversed(instances):
            _create_history(instance, user)
        queryset.delete()
        _trim_history(user)
    return deleted_count


def _validate_relation(field: models.Field[Any, Any], value: Any, user: AbstractBaseUser) -> None:
    if value is None or not isinstance(field, models.ForeignKey):
        return
    related_model = field.remote_field.model
    related = related_model._base_manager.filter(pk=value).first()
    if related is None:
        raise RestoreError(f"復元に必要な「{field.verbose_name}」が見つかりません。")
    if hasattr(related, "user_id") and related.user_id not in (None, user.pk):
        raise RestoreError(f"復元に必要な「{field.verbose_name}」を利用できません。")


def _restore_snapshot(
    model: type[models.Model],
    snapshot: dict[str, Any],
    user: AbstractBaseUser,
    *,
    overrides: dict[str, Any] | None = None,
) -> models.Model:
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("fields"), dict):
        raise RestoreError("復元データの形式が不正です。")

    try:
        original_pk = int(snapshot["pk"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RestoreError("復元データのIDが不正です。") from exc

    if model._base_manager.filter(pk=original_pk).exists():
        raise RestoreError("同じIDのデータが既に存在するため復元できません。")

    stored_fields = snapshot["fields"]
    allowed_fields = {
        field.attname: field
        for field in model._meta.concrete_fields
        if not field.primary_key and field.name != "user"
    }
    if not set(stored_fields).issubset(allowed_fields):
        raise RestoreError("復元データに未対応の項目があります。")

    values = dict(stored_fields)
    values.update(overrides or {})
    for key, value in values.items():
        field = allowed_fields.get(key)
        if field is None:
            raise RestoreError("復元データに未対応の項目があります。")
        _validate_relation(field, value, user)

    auto_values: dict[str, Any] = {}
    create_values: dict[str, Any] = {}
    for key, value in values.items():
        field = allowed_fields[key]
        if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
            auto_values[key] = value
        else:
            create_values[key] = value

    if any(field.name == "user" for field in model._meta.concrete_fields):
        create_values["user"] = user

    instance = model(pk=original_pk, **create_values)
    try:
        instance.save(force_insert=True)
        if auto_values:
            model._base_manager.filter(pk=original_pk).update(**auto_values)
            instance.refresh_from_db()
    except IntegrityError as exc:
        raise RestoreError("同じ内容のデータが既にあるため復元できません。") from exc
    return instance


def restore_deleted_item(deleted_item: DeletedItem, user: AbstractBaseUser) -> models.Model:
    """削除履歴を元のID・所有者で復元し、成功した履歴を取り除く。"""
    if deleted_item.user_id != user.pk:
        raise RestoreError("この削除履歴は復元できません。")
    spec = _SPECS_BY_KEY.get(deleted_item.object_type)
    if spec is None:
        raise RestoreError("この種類のデータは復元できません。")

    payload = deleted_item.payload
    if not isinstance(payload, dict) or payload.get("version") != SNAPSHOT_VERSION:
        raise RestoreError("この削除履歴の形式には対応していません。")
    relations = payload.get("relations", {})
    if not isinstance(relations, dict):
        raise RestoreError("復元データの形式が不正です。")

    with transaction.atomic():
        locked_item = DeletedItem.objects.select_for_update().get(pk=deleted_item.pk, user=user)
        restored = _restore_snapshot(spec.model, locked_item.payload["object"], user)

        if isinstance(restored, Habit):
            for record in relations.get("records", []):
                _restore_snapshot(HabitRecord, record, user, overrides={"habit_id": restored.pk})
        elif isinstance(restored, Task):
            for child in relations.get("recurring_instances", []):
                _restore_snapshot(Task, child, user, overrides={"parent_task_id": restored.pk})
        elif isinstance(restored, TempTaskSet):
            for item in relations.get("items", []):
                _restore_snapshot(TempTaskItem, item, user, overrides={"task_set_id": restored.pk})

        locked_item.delete()

    return restored
