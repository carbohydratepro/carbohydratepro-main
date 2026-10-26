"""日本の祝日判定と家計簿グラフへの受け渡し。"""
import json
from datetime import date

from django.test import TestCase

from app.expenses.selectors import build_daily_chart_data
from app.expenses.models import Transaction
from project.jp_holidays import holiday_labels, holidays_in_year, is_holiday


class JapaneseHolidayTest(TestCase):
    def test_2026_holidays_match_cabinet_office_calendar(self) -> None:
        expected = {
            date(2026, 1, 1), date(2026, 1, 12), date(2026, 2, 11), date(2026, 2, 23),
            date(2026, 3, 20), date(2026, 4, 29), date(2026, 5, 3), date(2026, 5, 4),
            date(2026, 5, 5), date(2026, 5, 6), date(2026, 7, 20), date(2026, 8, 11),
            date(2026, 9, 21), date(2026, 9, 22), date(2026, 9, 23), date(2026, 10, 12),
            date(2026, 11, 3), date(2026, 11, 23),
        }
        self.assertEqual(set(holidays_in_year(2026)), expected)

    def test_special_years_and_substitute_holidays(self) -> None:
        self.assertTrue(is_holiday(date(2019, 4, 30)))   # 国民の休日
        self.assertTrue(is_holiday(date(2019, 5, 6)))    # 振替休日
        self.assertTrue(is_holiday(date(2021, 7, 23)))   # 五輪特例のスポーツの日
        self.assertFalse(is_holiday(date(2021, 10, 11)))
        self.assertTrue(is_holiday(date(2021, 8, 9)))    # 山の日の振替
        self.assertFalse(is_holiday(date(2026, 3, 21)))

    def test_holiday_labels_filters_iso_dates(self) -> None:
        self.assertEqual(holiday_labels(["2026-05-05", "2026-05-07", "2026-05-06"]), ["2026-05-05", "2026-05-06"])

    def test_daily_chart_data_includes_holidays(self) -> None:
        expense_json, _ = build_daily_chart_data(Transaction.objects.none(), ["2026-11-02", "2026-11-03"])
        self.assertEqual(json.loads(expense_json)["holidays"], ["2026-11-03"])
