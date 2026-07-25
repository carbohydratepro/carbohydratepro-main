"""削除履歴と復元機能のテスト。"""

import json
from datetime import date
from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from app.deletion import archive_and_delete
from app.expenses.models import RecurringPayment, Transaction
from app.habit.models import Habit, HabitRecord
from app.memo.models import Memo, MemoType
from app.models import DeletedItem
from app.shopping.models import ShoppingItem
from app.task.models import Task, TempTaskItem, TempTaskSet
from tests.factories import (
    MemoFactory,
    MemoTypeFactory,
    RecurringPaymentFactory,
    TransactionFactory,
    UserFactory,
)


class TrashViewTest(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client = Client()
        self.client.force_login(self.user)

    def test_trash_requires_login(self) -> None:
        response = Client().get(reverse("trash"))
        self.assertEqual(response.status_code, 302)

    def test_delete_and_restore_memo(self) -> None:
        memo_type = MemoTypeFactory(user=self.user)
        memo = MemoFactory(
            user=self.user,
            memo_type=memo_type,
            title="戻したいメモ",
            content="削除前の本文",
            is_favorite=True,
        )
        memo_id = memo.pk
        created_date = memo.created_date

        response = self.client.post(reverse("delete_memo", kwargs={"memo_id": memo_id}))

        self.assertRedirects(response, reverse("memo_list"))
        self.assertFalse(Memo.objects.filter(pk=memo_id).exists())
        deleted_item = DeletedItem.objects.get(user=self.user)
        self.assertEqual(deleted_item.object_label, "メモ")
        self.assertEqual(deleted_item.object_name, "戻したいメモ")

        response = self.client.post(
            reverse("restore_deleted_item", kwargs={"deleted_item_id": deleted_item.pk})
        )

        self.assertRedirects(response, reverse("trash"))
        restored = Memo.objects.get(pk=memo_id)
        self.assertEqual(restored.user, self.user)
        self.assertEqual(restored.memo_type, memo_type)
        self.assertEqual(restored.content, "削除前の本文")
        self.assertTrue(restored.is_favorite)
        self.assertEqual(
            restored.created_date.replace(
                microsecond=restored.created_date.microsecond // 1000 * 1000
            ),
            created_date.replace(microsecond=created_date.microsecond // 1000 * 1000),
        )
        self.assertFalse(DeletedItem.objects.filter(pk=deleted_item.pk).exists())

    def test_only_latest_ten_items_are_retained_per_user(self) -> None:
        memo_type = MemoTypeFactory(user=self.user)
        other_user = UserFactory()
        other_memo = MemoFactory(user=other_user)
        archive_and_delete(other_memo, other_user)

        for index in range(12):
            memo = MemoFactory(
                user=self.user,
                memo_type=memo_type,
                title=f"履歴{index}",
            )
            archive_and_delete(memo, self.user)

        names = list(
            DeletedItem.objects.filter(user=self.user).values_list("object_name", flat=True)
        )
        self.assertEqual(len(names), 10)
        self.assertEqual(names[0], "履歴11")
        self.assertNotIn("履歴0", names)
        self.assertNotIn("履歴1", names)
        self.assertEqual(DeletedItem.objects.filter(user=other_user).count(), 1)

    def test_other_users_history_is_hidden_and_cannot_be_restored(self) -> None:
        other_user = UserFactory()
        memo = MemoFactory(user=other_user, title="他人のメモ")
        deleted_item = archive_and_delete(memo, other_user)

        page = self.client.get(reverse("trash"))
        self.assertNotContains(page, "他人のメモ")

        response = self.client.post(
            reverse("restore_deleted_item", kwargs={"deleted_item_id": deleted_item.pk})
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(DeletedItem.objects.filter(pk=deleted_item.pk).exists())

    def test_failed_restore_keeps_history(self) -> None:
        memo_type = MemoType.objects.create(user=self.user, name="消える種別")
        memo = Memo.objects.create(user=self.user, memo_type=memo_type, title="復元待ち")
        memo_id = memo.pk
        deleted_item = archive_and_delete(memo, self.user)
        memo_type.delete()

        response = self.client.post(
            reverse("restore_deleted_item", kwargs={"deleted_item_id": deleted_item.pk})
        )

        self.assertRedirects(response, reverse("trash"))
        self.assertFalse(Memo.objects.filter(pk=memo_id).exists())
        self.assertTrue(DeletedItem.objects.filter(pk=deleted_item.pk).exists())


class RelatedDataRestoreTest(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client = Client()
        self.client.force_login(self.user)

    def _restore(self, deleted_item: DeletedItem) -> None:
        response = self.client.post(
            reverse("restore_deleted_item", kwargs={"deleted_item_id": deleted_item.pk})
        )
        self.assertRedirects(response, reverse("trash"))

    def test_habit_records_are_restored_with_habit(self) -> None:
        habit = Habit.objects.create(user=self.user, title="朝の運動", frequency="daily")
        record = HabitRecord.objects.create(habit=habit, date=date(2026, 7, 24), coefficient=3)
        habit_id = habit.pk
        record_id = record.pk
        deleted_item = archive_and_delete(habit, self.user)

        self.assertFalse(HabitRecord.objects.filter(pk=record_id).exists())
        self._restore(deleted_item)

        restored_record = HabitRecord.objects.get(pk=record_id)
        self.assertEqual(restored_record.habit_id, habit_id)
        self.assertEqual(restored_record.coefficient, 3)

    def test_transaction_foreign_keys_and_decimal_are_restored(self) -> None:
        transaction = TransactionFactory(
            user=self.user,
            amount=Decimal("1234.56"),
            purpose="昼食",
            purpose_description="復元する明細",
        )
        transaction_id = transaction.pk
        category_id = transaction.category_id
        payment_method_id = transaction.payment_method_id
        deleted_item = archive_and_delete(transaction, self.user)

        self._restore(deleted_item)

        restored = Transaction.objects.get(pk=transaction_id)
        self.assertEqual(restored.amount, Decimal("1234.56"))
        self.assertEqual(restored.category_id, category_id)
        self.assertEqual(restored.payment_method_id, payment_method_id)
        self.assertEqual(restored.purpose_description, "復元する明細")

    def test_recurring_payment_array_fields_are_restored(self) -> None:
        recurring = RecurringPaymentFactory(
            user=self.user,
            frequency="weekly",
            days_of_week=[0, 2, 4],
            days_of_month=[],
        )
        recurring_id = recurring.pk
        deleted_item = archive_and_delete(recurring, self.user)

        self._restore(deleted_item)

        restored = RecurringPayment.objects.get(pk=recurring_id)
        self.assertEqual(restored.frequency, "weekly")
        self.assertEqual(restored.days_of_week, [0, 2, 4])
        self.assertEqual(restored.days_of_month, [])

    def test_recurring_task_children_are_restored_with_parent(self) -> None:
        parent = Task.objects.create(
            user=self.user,
            title="繰り返し予定",
            frequency="daily",
            repeat_interval=1,
        )
        child = Task.objects.create(
            user=self.user,
            title="繰り返し予定",
            parent_task=parent,
        )
        parent_id = parent.pk
        child_id = child.pk
        deleted_item = archive_and_delete(parent, self.user)

        self.assertFalse(Task.objects.filter(pk=child_id).exists())
        self._restore(deleted_item)

        restored_child = Task.objects.get(pk=child_id)
        self.assertEqual(restored_child.parent_task_id, parent_id)

    def test_temp_task_set_items_are_restored_with_set(self) -> None:
        task_set = TempTaskSet.objects.create(user=self.user, name="仕事")
        item = TempTaskItem.objects.create(
            user=self.user,
            task_set=task_set,
            title="資料を作る",
            status="doing",
        )
        set_id = task_set.pk
        item_id = item.pk
        deleted_item = archive_and_delete(task_set, self.user)

        self._restore(deleted_item)

        restored_item = TempTaskItem.objects.get(pk=item_id)
        self.assertEqual(restored_item.task_set_id, set_id)
        self.assertEqual(restored_item.status, "doing")


class TrashDeletionEndpointTest(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client = Client()
        self.client.force_login(self.user)

    def test_bulk_delete_creates_restorable_history(self) -> None:
        memo_type = MemoTypeFactory(user=self.user)
        memos = [MemoFactory(user=self.user, memo_type=memo_type) for _ in range(2)]
        ids = [memo.pk for memo in memos]

        response = self.client.post(
            reverse("bulk_delete_memos"),
            data=json.dumps({"ids": ids}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["deleted"], 2)
        self.assertEqual(DeletedItem.objects.filter(user=self.user).count(), 2)

    def test_temp_task_delete_returns_restore_url_and_restores_via_json(self) -> None:
        task_set = TempTaskSet.objects.create(user=self.user, name="デフォルト")
        task = TempTaskItem.objects.create(
            user=self.user,
            task_set=task_set,
            title="取り消すタスク",
        )

        delete_response = self.client.delete(
            reverse("temp_task_detail_api", kwargs={"task_id": task.pk}),
            content_type="application/json",
        )

        self.assertEqual(delete_response.status_code, 200)
        restore_path = delete_response.json()["restore_url"]
        restore_response = self.client.post(
            restore_path,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(restore_response.status_code, 200)
        self.assertTrue(restore_response.json()["success"])
        self.assertTrue(TempTaskItem.objects.filter(pk=task.pk, user=self.user).exists())

    def test_clear_checked_shopping_items_creates_history(self) -> None:
        items = [
            ShoppingItem.objects.create(
                user=self.user,
                title=f"購入済み{index}",
                frequency="one_time",
                is_checked=True,
            )
            for index in range(2)
        ]
        ShoppingItem.objects.create(
            user=self.user,
            title="未購入",
            frequency="one_time",
            is_checked=False,
        )

        response = self.client.post(reverse("clear_checked_shopping"))

        self.assertRedirects(response, reverse("shopping_list"))
        self.assertEqual(ShoppingItem.objects.filter(pk__in=[item.pk for item in items]).count(), 0)
        self.assertEqual(
            DeletedItem.objects.filter(user=self.user, object_type="shopping_item").count(),
            2,
        )
