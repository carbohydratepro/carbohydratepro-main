"""2026-07-26 機能修正の回帰テスト。"""

from __future__ import annotations

import json
from decimal import Decimal

from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from app.expenses import selectors as expense_selectors
from app.expenses.forms import RecurringPaymentForm, TransactionForm
from app.expenses.models import Category, PaymentMethod, Transaction
from app.task.forms import TaskForm
from app.task.models import TaskLabel
from app.templatetags.app_filters import money_size_class
from tests.factories import UserFactory


class ExpenseFeatureFixTest(TestCase):
    """家計簿の詳細絞り込み・表示順・グラフ改善を検証する。"""

    def setUp(self) -> None:
        self.user = UserFactory()
        self.client = Client()
        self.client.force_login(self.user)
        self.food = Category.objects.create(user=self.user, name="食費", sort_order=0)
        self.transport = Category.objects.create(
            user=self.user,
            name="交通費",
            sort_order=1,
        )
        self.card = PaymentMethod.objects.create(
            user=self.user,
            name="クレジットカード",
            sort_order=0,
        )
        self.cash = PaymentMethod.objects.create(user=self.user, name="現金", sort_order=1)
        self.food_card = self._create_transaction("外食", self.food, self.card)
        self.transport_card = self._create_transaction("電車", self.transport, self.card)
        self.food_cash = self._create_transaction("食材", self.food, self.cash)

    def _create_transaction(
        self,
        purpose: str,
        category: Category,
        payment_method: PaymentMethod,
    ) -> Transaction:
        return Transaction.objects.create(
            user=self.user,
            amount=Decimal("1000"),
            date=timezone.now(),
            transaction_type="expense",
            payment_method=payment_method,
            purpose=purpose,
            major_category="variable",
            category=category,
            purpose_description="",
        )

    def test_multiple_include_and_exclude_filters_are_combined(self) -> None:
        """同一種別はOR、異なる種別とNOTはANDで組み合わさる。"""
        start, end, _ = expense_selectors.get_date_range(
            timezone.localdate().strftime("%Y-%m")
        )
        result = expense_selectors.get_transactions(
            self.user,
            start,
            end,
            category_ids=[self.food.pk, self.transport.pk],
            excluded_payment_method_ids=[self.cash.pk],
        )

        self.assertQuerySetEqual(
            result.order_by("pk"),
            [self.food_card, self.transport_card],
        )

    def test_expense_list_preserves_repeated_filter_conditions(self) -> None:
        response = self.client.get(
            reverse("expense_list"),
            {
                "target_date": timezone.localdate().strftime("%Y-%m"),
                "category": [self.food.pk, self.transport.pk],
                "exclude_payment_method": [self.cash.pk],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["filter_categories"], [self.food.pk, self.transport.pk])
        self.assertEqual(response.context["excluded_payment_methods"], [self.cash.pk])
        self.assertContains(response, "外食")
        self.assertContains(response, "電車")
        self.assertNotContains(response, "食材")

    def test_required_choice_fields_do_not_show_blank_option(self) -> None:
        transaction_form = TransactionForm(user=self.user)
        recurring_form = RecurringPaymentForm(user=self.user)

        for form in (transaction_form, recurring_form):
            self.assertNotIn("", dict(form.fields["transaction_type"].choices))
            self.assertNotIn("", dict(form.fields["major_category"].choices))

    def test_chart_data_contains_filter_values_and_balance_label(self) -> None:
        transactions = Transaction.objects.filter(user=self.user)
        category_data = json.loads(expense_selectors.build_category_chart_data(transactions))
        major_data = json.loads(expense_selectors.build_major_category_chart_data(transactions))
        _, balance_json = expense_selectors.build_daily_chart_data(
            transactions,
            [timezone.localdate().isoformat()],
        )

        self.assertIn(str(self.food.pk), category_data["filterValues"])
        self.assertEqual(major_data["filterValues"], ["variable"])
        self.assertEqual(json.loads(balance_json)["datasets"][0]["label"], "収支")

    def test_new_settings_are_appended_and_can_be_reordered(self) -> None:
        response = self.client.post(
            reverse("expenses_settings"),
            {"payment": "1", "payment-name": "電子マネー"},
        )
        self.assertRedirects(response, reverse("expenses_settings"))
        electronic = PaymentMethod.objects.get(user=self.user, name="電子マネー")
        self.assertGreater(electronic.sort_order, self.cash.sort_order)

        response = self.client.post(
            reverse("expenses_settings"),
            {
                "payment_id": electronic.pk,
                "move_payment": "1",
                "direction": "up",
            },
        )
        self.assertRedirects(response, reverse("expenses_settings"))
        names = list(PaymentMethod.objects.filter(user=self.user).values_list("name", flat=True))
        self.assertEqual(names, ["クレジットカード", "電子マネー", "現金"])


class ScheduleFeatureFixTest(TestCase):
    """スケジュールの週開始・表示順・既定ラベルを検証する。"""

    def setUp(self) -> None:
        self.user = UserFactory()
        self.client = Client()
        self.client.force_login(self.user)
        self.work = TaskLabel.objects.create(
            user=self.user,
            name="仕事",
            color="#112233",
            sort_order=0,
        )
        self.private = TaskLabel.objects.create(
            user=self.user,
            name="プライベート",
            color="#445566",
            sort_order=1,
        )

    def test_week_start_setting_changes_calendar_order(self) -> None:
        response = self.client.post(
            reverse("task_settings"),
            {"update_week_start": "1", "week_start": "monday"},
        )
        self.assertRedirects(response, reverse("task_settings"))
        self.assertEqual(self.client.session["task_week_start"], "monday")

        calendar_response = self.client.get(reverse("task_list"))
        self.assertEqual(calendar_response.context["weekday_labels"][0], "月")

    def test_default_label_is_used_by_new_task_form(self) -> None:
        response = self.client.post(
            reverse("task_settings"),
            {"set_default_label": "1", "label_id": self.private.pk},
        )
        self.assertRedirects(response, reverse("task_settings"))
        self.private.refresh_from_db()
        self.assertTrue(self.private.is_default)
        self.assertEqual(TaskForm(user=self.user).fields["label"].initial, self.private)

    def test_label_can_be_reordered_without_touching_other_user(self) -> None:
        other_user = UserFactory()
        other_label = TaskLabel.objects.create(
            user=other_user,
            name="他ユーザー",
            sort_order=0,
        )
        response = self.client.post(
            reverse("task_settings"),
            {"move_label": "1", "label_id": self.private.pk, "direction": "up"},
        )
        self.assertRedirects(response, reverse("task_settings"))

        names = list(TaskLabel.objects.filter(user=self.user).values_list("name", flat=True))
        self.assertEqual(names, ["プライベート", "仕事"])
        other_label.refresh_from_db()
        self.assertEqual(other_label.sort_order, 0)

    def test_settings_has_explicit_edit_and_default_controls(self) -> None:
        response = self.client.get(reverse("task_settings"))
        self.assertContains(response, "仕事を編集")
        self.assertContains(response, "仕事を既定にする")
        self.assertContains(response, "保存")


class ResponsiveAndDashboardFixTest(SimpleTestCase):
    """金額表示とホーム簡易情報の表示契約を検証する。"""

    def test_money_size_class_changes_at_eight_digits(self) -> None:
        self.assertEqual(money_size_class(9_999_999), "money-value")
        self.assertEqual(money_size_class(10_000_000), "money-value money-value-long")


class DashboardBriefInfoTest(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory()
        self.client = Client()
        self.client.force_login(self.user)

    def test_dashboard_shows_brief_information_and_opt_in_weather(self) -> None:
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "今日のひとこと")
        self.assertContains(response, "今日は何の日を見る")
        self.assertContains(response, "現在地の天気")
        self.assertContains(response, "天気を表示")
        self.assertContains(response, "Open-Meteo")
