"""画面表示の問い合わせ回数削減（お問い合わせ#15）と結果の正しさ。"""
import json
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.test import TestCase

from app.expenses.models import Transaction
from app.expenses.selectors import build_daily_chart_data
from app.task.selectors import build_calendar_data, get_month_tasks
from tests.factories import TaskFactory, TransactionFactory, UserFactory

JST = ZoneInfo("Asia/Tokyo")


class DailyChartAggregationTest(TestCase):
    def test_totals_follow_japan_date_and_use_single_query(self) -> None:
        user = UserFactory()
        TransactionFactory(user=user, amount=Decimal("1200"), date=datetime(2026, 11, 2, 23, 30, tzinfo=JST))
        TransactionFactory(user=user, amount=Decimal("300"), date=datetime(2026, 11, 3, 0, 10, tzinfo=JST))
        TransactionFactory(
            user=user, amount=Decimal("5000"), transaction_type="income", date=datetime(2026, 11, 3, 9, 0, tzinfo=JST),
        )
        labels = ["2026-11-01", "2026-11-02", "2026-11-03"]

        with self.assertNumQueries(1):
            expense_json, balance_json = build_daily_chart_data(Transaction.objects.filter(user=user), labels)

        self.assertEqual(json.loads(expense_json)["datasets"][0]["data"], [0.0, 1200.0, 300.0])
        self.assertEqual(json.loads(balance_json)["datasets"][0]["data"], [0.0, -1200.0, 3500.0])


class MonthCalendarQueryTest(TestCase):
    def test_calendar_fetches_tasks_once_and_places_them_on_each_day(self) -> None:
        user = UserFactory()
        TaskFactory(
            user=user, title="連休", start_date=datetime(2026, 11, 2, 10, 0, tzinfo=JST),
            end_date=datetime(2026, 11, 4, 9, 0, tzinfo=JST),
        )
        TaskFactory(user=user, title="締切のみ", end_date=datetime(2026, 11, 3, 18, 0, tzinfo=JST))
        TaskFactory(user=user, title="朝", start_date=datetime(2026, 11, 3, 7, 0, tzinfo=JST),
                    end_date=datetime(2026, 11, 3, 8, 0, tzinfo=JST))
        month_tasks = get_month_tasks(
            user, datetime(2026, 10, 25, tzinfo=JST), datetime(2026, 12, 7, 23, 59, 59, tzinfo=JST),
        )

        with self.assertNumQueries(1):
            calendar_data, _ = build_calendar_data(month_tasks, 2026, 11, "sunday")

        days = {(d["month"], d["day"]): d for week in calendar_data for d in week}
        # 終了日のみのタスクは従来どおり終了日までの各日に表示される
        self.assertEqual([t.title for t in days[(11, 2)]["tasks"]], ["連休", "締切のみ"])
        self.assertEqual([t.title for t in days[(11, 3)]["tasks"]], ["連休", "朝", "締切のみ"])
        self.assertEqual([t.title for t in days[(11, 4)]["tasks"]], ["連休"])
        self.assertEqual(days[(11, 5)]["task_count"], 0)
