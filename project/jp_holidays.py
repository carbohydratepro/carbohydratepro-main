"""日本の祝日判定（外部ライブラリなし）。

「国民の祝日に関する法律」の現行規定（2000年以降のハッピーマンデー等）と、
2019〜2021年の特例日を扱う。春分・秋分は1980〜2099年で有効な近似式を使う。
"""
from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache


def _nth_monday(year: int, month: int, nth: int) -> date:
    first = date(year, month, 1)
    offset = (0 - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (nth - 1))


def _equinox_day(year: int, base: float) -> int:
    return int(base + 0.242194 * (year - 1980) - (year - 1980) // 4)


def _base_holidays(year: int) -> set[date]:
    days = {
        date(year, 1, 1),
        _nth_monday(year, 1, 2),  # 成人の日
        date(year, 2, 11),
        date(year, 3, _equinox_day(year, 20.8431)),  # 春分の日
        date(year, 4, 29),
        date(year, 5, 3),
        date(year, 5, 4),
        date(year, 5, 5),
        _nth_monday(year, 9, 3),  # 敬老の日
        date(year, 9, _equinox_day(year, 23.2488)),  # 秋分の日
        date(year, 11, 3),
        date(year, 11, 23),
    }
    if year >= 2020:
        days.add(date(year, 2, 23))  # 天皇誕生日
    elif year <= 2018:
        days.add(date(year, 12, 23))

    # 海の日・スポーツの日・山の日（2020・2021年は東京五輪の特例で移動）
    special_moves = {
        2020: (date(2020, 7, 23), date(2020, 7, 24), date(2020, 8, 10)),
        2021: (date(2021, 7, 22), date(2021, 7, 23), date(2021, 8, 8)),
    }
    if year in special_moves:
        days.update(special_moves[year])
    else:
        days.add(_nth_monday(year, 7, 3))
        days.add(_nth_monday(year, 10, 2))
        if year >= 2016:
            days.add(date(year, 8, 11))

    if year == 2019:  # 天皇の即位に伴う特例
        days.update({date(2019, 5, 1), date(2019, 10, 22)})
    return days


@lru_cache(maxsize=64)
def holidays_in_year(year: int) -> frozenset[date]:
    """指定年の祝日（振替休日・国民の休日を含む）を返す。"""
    days = _base_holidays(year)

    # 国民の休日: 前後を祝日に挟まれた平日
    for day in sorted(days):
        between = day + timedelta(days=1)
        if between not in days and between + timedelta(days=1) in days and between.weekday() != 6:
            days.add(between)

    # 振替休日: 日曜の祝日の後、最初の祝日でない日
    for day in sorted(days):
        if day.weekday() == 6:
            substitute = day + timedelta(days=1)
            while substitute in days:
                substitute += timedelta(days=1)
            days.add(substitute)
    return frozenset(days)


def is_holiday(day: date) -> bool:
    return day in holidays_in_year(day.year)


def holiday_labels(date_labels: list[str]) -> list[str]:
    """日付ラベル（YYYY-MM-DD）のうち祝日に当たるものを返す。"""
    return [label for label in date_labels if is_holiday(date.fromisoformat(label))]
