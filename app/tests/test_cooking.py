"""料理記録機能のテスト。"""

from __future__ import annotations

import tempfile
from datetime import date

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.cooking.forms import CookingDishForm
from app.cooking.models import CookingDish, CookingHistory, CookingStep
from app.models import DeletedItem
from tests.factories import UserFactory


def _step_management(total: int = 1, initial: int = 0) -> dict[str, str]:
    return {
        "steps-TOTAL_FORMS": str(total),
        "steps-INITIAL_FORMS": str(initial),
        "steps-MIN_NUM_FORMS": "0",
        "steps-MAX_NUM_FORMS": "10",
    }


def _dish_payload(**overrides: str) -> dict[str, str]:
    data = {
        "title": "チキンカレー",
        "ingredients": "鶏肉 300g\n玉ねぎ 1個",
        "servings": "2",
        "cooking_time_minutes": "45",
        "recipe_mode": "single",
        "recipe_text": "材料を炒めて煮込む",
        "notes": "翌日は辛さを足す",
        **_step_management(),
        "steps-0-position": "1",
        "steps-0-instruction": "",
    }
    data.update(overrides)
    return data


class CookingTestBase(TestCase):
    def setUp(self) -> None:
        self.media_directory = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.addCleanup(self.media_directory.cleanup)
        self.user = UserFactory()
        self.client = Client()
        self.client.force_login(self.user)


class CookingCrudTest(CookingTestBase):
    def test_pages_require_login(self) -> None:
        response = Client().get(reverse("cooking_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_minimal_dish_can_be_created_with_zero_history(self) -> None:
        response = self.client.post(reverse("cooking_create"), _dish_payload())

        dish = CookingDish.objects.get(user=self.user)
        self.assertRedirects(response, reverse("cooking_detail", kwargs={"dish_id": dish.pk}))
        self.assertEqual(dish.title, "チキンカレー")
        self.assertEqual(dish.histories.count(), 0)
        self.assertEqual(dish.steps.count(), 0)

        list_response = self.client.get(reverse("cooking_list"))
        self.assertContains(list_response, "0回")
        self.assertContains(list_response, "まだ作っていません")

    def test_step_recipe_is_saved_in_submitted_order(self) -> None:
        data = _dish_payload(
            recipe_mode="steps",
            recipe_text="",
            **_step_management(total=2),
            **{
                "steps-0-position": "2",
                "steps-0-instruction": "弱火で煮込む",
                "steps-1-position": "1",
                "steps-1-instruction": "材料を切る",
            },
        )

        response = self.client.post(reverse("cooking_create"), data)

        dish = CookingDish.objects.get(user=self.user)
        self.assertRedirects(response, reverse("cooking_detail", kwargs={"dish_id": dish.pk}))
        self.assertEqual(
            list(dish.steps.values_list("position", "instruction")),
            [(1, "材料を切る"), (2, "弱火で煮込む")],
        )

    def test_edit_updates_dish_reorders_steps_and_deletes_a_step(self) -> None:
        dish = CookingDish.objects.create(
            user=self.user,
            title="編集前",
            recipe_mode="steps",
        )
        first = CookingStep.objects.create(dish=dish, position=1, instruction="切る")
        second = CookingStep.objects.create(dish=dish, position=2, instruction="煮る")
        data = _dish_payload(
            title="編集後",
            recipe_mode="steps",
            recipe_text="",
            **_step_management(total=2, initial=2),
            **{
                "steps-0-id": str(first.pk),
                "steps-0-position": "1",
                "steps-0-instruction": "切る",
                "steps-0-DELETE": "on",
                "steps-1-id": str(second.pk),
                "steps-1-position": "1",
                "steps-1-instruction": "じっくり煮る",
            },
        )

        response = self.client.post(reverse("cooking_edit", args=[dish.pk]), data)

        self.assertRedirects(response, reverse("cooking_detail", args=[dish.pk]))
        dish.refresh_from_db()
        self.assertEqual(dish.title, "編集後")
        self.assertEqual(
            list(dish.steps.values_list("position", "instruction")),
            [(1, "じっくり煮る")],
        )

    def test_step_mode_requires_at_least_one_instruction(self) -> None:
        response = self.client.post(
            reverse("cooking_create"),
            _dish_payload(recipe_mode="steps", recipe_text=""),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "手順を1つ以上入力してください")
        self.assertFalse(CookingDish.objects.filter(user=self.user).exists())

    def test_at_most_ten_steps_are_accepted(self) -> None:
        data = _dish_payload(recipe_mode="steps", recipe_text="", **_step_management(total=11))
        for index in range(11):
            data[f"steps-{index}-position"] = str(min(index + 1, 10))
            data[f"steps-{index}-instruction"] = f"手順{index + 1}"

        response = self.client.post(reverse("cooking_create"), data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "最大で 10 個")
        self.assertFalse(CookingDish.objects.filter(user=self.user).exists())

    def test_dish_can_be_searched_by_title_or_ingredients(self) -> None:
        CookingDish.objects.create(user=self.user, title="親子丼", ingredients="鶏肉\n卵")
        CookingDish.objects.create(user=self.user, title="味噌汁", ingredients="豆腐\nわかめ")

        by_title = self.client.get(reverse("cooking_list"), {"search": "親子"})
        self.assertContains(by_title, "親子丼")
        self.assertNotContains(by_title, "味噌汁")

        by_ingredient = self.client.get(reverse("cooking_list"), {"search": "豆腐"})
        self.assertContains(by_ingredient, "味噌汁")
        self.assertNotContains(by_ingredient, "親子丼")

    def test_detail_escapes_user_content(self) -> None:
        dish = CookingDish.objects.create(
            user=self.user,
            title="安全な料理",
            recipe_text='<script>alert("xss")</script>',
        )

        response = self.client.get(reverse("cooking_detail", kwargs={"dish_id": dish.pk}))

        self.assertNotContains(response, '<script>alert("xss")</script>', html=True)
        self.assertContains(response, "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;")

    def test_other_users_cannot_view_or_change_dish(self) -> None:
        other_user = UserFactory()
        dish = CookingDish.objects.create(user=other_user, title="他人の料理")
        history = CookingHistory.objects.create(dish=dish, cooked_on=date(2026, 7, 20), count=1)

        self.assertEqual(
            self.client.get(reverse("cooking_detail", args=[dish.pk])).status_code, 404
        )
        self.assertEqual(self.client.get(reverse("cooking_edit", args=[dish.pk])).status_code, 404)
        self.assertEqual(
            self.client.post(reverse("cooking_delete", args=[dish.pk])).status_code, 404
        )
        self.assertEqual(
            self.client.post(reverse("cooking_record_today", args=[dish.pk])).status_code, 404
        )
        self.assertEqual(
            self.client.post(
                reverse("cooking_history_update", args=[dish.pk, history.pk])
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                reverse("cooking_history_delete", args=[dish.pk, history.pk])
            ).status_code,
            404,
        )
        self.assertTrue(CookingDish.objects.filter(pk=dish.pk).exists())


class CookingImageValidationTest(CookingTestBase):
    def test_non_image_upload_is_rejected(self) -> None:
        upload = SimpleUploadedFile("recipe.jpg", b"not an image", content_type="image/jpeg")
        form = CookingDishForm(
            data={"title": "偽画像", "recipe_mode": "single"},
            files={"photo_1": upload},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("画像形式を確認できません", str(form.errors["photo_1"]))

    def test_image_larger_than_five_megabytes_is_rejected(self) -> None:
        upload = SimpleUploadedFile(
            "large.png",
            b"\x89PNG\r\n\x1a\n" + b"0" * (5 * 1024 * 1024),
            content_type="image/png",
        )
        form = CookingDishForm(
            data={"title": "大きな画像", "recipe_mode": "single"},
            files={"photo_1": upload},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("5MB以下", str(form.errors["photo_1"]))


class CookingHistoryTest(CookingTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.dish = CookingDish.objects.create(user=self.user, title="オムライス")

    def test_today_button_increments_the_same_day(self) -> None:
        url = reverse("cooking_record_today", args=[self.dish.pk])

        self.client.post(url)
        self.client.post(url)

        history = CookingHistory.objects.get(dish=self.dish)
        self.assertEqual(history.cooked_on, timezone.localdate())
        self.assertEqual(history.count, 2)

    def test_today_button_does_not_exceed_daily_limit(self) -> None:
        CookingHistory.objects.create(
            dish=self.dish,
            cooked_on=timezone.localdate(),
            count=999,
        )

        response = self.client.post(reverse("cooking_record_today", args=[self.dish.pk]))

        self.assertRedirects(response, reverse("cooking_detail", args=[self.dish.pk]))
        self.assertEqual(
            CookingHistory.objects.get(dish=self.dish, cooked_on=timezone.localdate()).count,
            999,
        )
        response_messages = list(response.wsgi_request._messages)
        self.assertTrue(any("999回まで" in str(message) for message in response_messages))

    def test_history_can_be_added_updated_and_deleted(self) -> None:
        add_response = self.client.post(
            reverse("cooking_history_add", args=[self.dish.pk]),
            {"cooked_on": "2026-07-01", "count": "2", "note": "家族分"},
        )
        history = CookingHistory.objects.get(dish=self.dish)
        self.assertRedirects(add_response, reverse("cooking_detail", args=[self.dish.pk]))

        update_response = self.client.post(
            reverse("cooking_history_update", args=[self.dish.pk, history.pk]),
            {"cooked_on": "2026-07-02", "count": "3", "note": "作り置き"},
        )
        history.refresh_from_db()
        self.assertRedirects(update_response, reverse("cooking_detail", args=[self.dish.pk]))
        self.assertEqual(history.cooked_on, date(2026, 7, 2))
        self.assertEqual(history.count, 3)

        delete_response = self.client.post(
            reverse("cooking_history_delete", args=[self.dish.pk, history.pk])
        )
        self.assertRedirects(delete_response, reverse("cooking_detail", args=[self.dish.pk]))
        self.assertFalse(CookingHistory.objects.filter(pk=history.pk).exists())

    def test_duplicate_day_is_rejected_without_overwriting(self) -> None:
        CookingHistory.objects.create(dish=self.dish, cooked_on=date(2026, 7, 1), count=2)

        response = self.client.post(
            reverse("cooking_history_add", args=[self.dish.pk]),
            {"cooked_on": "2026-07-01", "count": "5", "note": "重複"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "この日付の記録は既にあります")
        self.assertEqual(CookingHistory.objects.get(dish=self.dish).count, 2)

    def test_database_rejects_zero_count(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            CookingHistory.objects.create(dish=self.dish, cooked_on=date(2026, 7, 3), count=0)

        with self.assertRaises(IntegrityError), transaction.atomic():
            CookingHistory.objects.create(dish=self.dish, cooked_on=date(2026, 7, 4), count=1000)


class CookingTrashTest(CookingTestBase):
    def test_delete_and_restore_includes_steps_histories_and_photo_names(self) -> None:
        dish = CookingDish.objects.create(
            user=self.user,
            title="復元する料理",
            recipe_mode="steps",
            photo_1="cooking/1/dish.jpg",
        )
        step = CookingStep.objects.create(
            dish=dish,
            position=1,
            instruction="混ぜる",
            photo_1="cooking/1/step.jpg",
        )
        history = CookingHistory.objects.create(dish=dish, cooked_on=date(2026, 7, 10), count=4)
        dish_id = dish.pk
        step_id = step.pk
        history_id = history.pk

        delete_response = self.client.post(reverse("cooking_delete", args=[dish.pk]))

        self.assertRedirects(delete_response, reverse("cooking_list"))
        self.assertFalse(CookingDish.objects.filter(pk=dish_id).exists())
        deleted_item = DeletedItem.objects.get(user=self.user, object_type="cooking_dish")

        restore_response = self.client.post(reverse("restore_deleted_item", args=[deleted_item.pk]))

        self.assertRedirects(restore_response, reverse("trash"))
        restored = CookingDish.objects.get(pk=dish_id)
        self.assertEqual(restored.photo_1.name, "cooking/1/dish.jpg")
        self.assertEqual(CookingStep.objects.get(pk=step_id).photo_1.name, "cooking/1/step.jpg")
        self.assertEqual(CookingHistory.objects.get(pk=history_id).count, 4)
        self.assertFalse(DeletedItem.objects.filter(pk=deleted_item.pk).exists())


class CookingModelValidationTest(CookingTestBase):
    def test_servings_and_cooking_time_limits_are_validated(self) -> None:
        dish = CookingDish(user=self.user, title="範囲外", servings=100, cooking_time_minutes=1441)

        with self.assertRaises(ValidationError) as context:
            dish.full_clean()

        self.assertIn("servings", context.exception.message_dict)
        self.assertIn("cooking_time_minutes", context.exception.message_dict)
