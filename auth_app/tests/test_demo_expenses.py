"""家計簿デモが実画面の閲覧機能と同期していることを検証する。"""

from __future__ import annotations

import json

from django.test import Client, TestCase
from django.urls import reverse


class DemoExpensesTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_demo_expenses_has_comparison_and_filterable_chart_data(self) -> None:
        response = self.client.get(reverse("demo_expenses"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["comparison_average_month_count"], 3)
        self.assertEqual(
            json.loads(response.context["comparison_data_json"])["labels"],
            ["2026年3月", "2026年2月", "全期間平均"],
        )
        category_data = json.loads(response.context["category_data_json"])
        self.assertIn("4", category_data["filterValues"])
        self.assertContains(response, "先月・全期間平均と比較")

    def test_demo_expenses_applies_multiple_and_exclude_filters(self) -> None:
        response = self.client.get(
            reverse("demo_expenses"),
            {
                "target_date": "2026-03",
                "category": [1, 2],
                "exclude_payment_method": [2],
            },
        )

        self.assertEqual(response.context["transactions_count"], 1)
        self.assertContains(response, "スーパー（食材）")
        self.assertNotContains(response, "ランチ")
        self.assertNotContains(response, "カフェ")

    def test_demo_expenses_supports_year_view(self) -> None:
        response = self.client.get(
            reverse("demo_expenses"),
            {"view_mode": "year", "target_date": "2026"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["view_mode"], "year")
        self.assertContains(response, 'id="monthlyBarChart"')
        monthly_data = json.loads(response.context["monthly_chart_data_json"])
        self.assertGreater(monthly_data["datasets"][1]["data"][2], 0)

    def test_demo_chart_filter_request_returns_only_transaction_list(self) -> None:
        response = self.client.get(
            reverse("demo_expenses"),
            {"target_date": "2026-03", "category": 4},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/expenses/_transaction_list.html")
        self.assertTemplateNotUsed(response, "app/expenses/list.html")
        self.assertContains(response, "家賃")
        self.assertNotContains(response, "categoryPieChart")
