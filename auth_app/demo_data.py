"""
デモ画面用のフェイクデータを生成するモジュール。
実際のモデルインスタンスに似た属性・メソッドを持つ軽量クラスを使用する。
"""
from __future__ import annotations

import calendar as cal_module
import json
from datetime import date, datetime, timedelta
from django.core.paginator import Paginator
from django.http import QueryDict

from project.utils import CHART_COLORS, MAJOR_CATEGORY_LABELS


# ---------------------------------------------------------------------------
# 汎用フェイクオブジェクトクラス
# ---------------------------------------------------------------------------

class FakeTransaction:
    _MAJOR_CAT = {'variable': '変動費', 'fixed': '固定費', 'special': '特別費'}
    _TRANS_TYPE = {'income': '収入', 'expense': '支出', 'no_change': '変動なし'}

    def __init__(self, id: int, purpose: str, date_val: date, amount: int,
                 transaction_type: str, payment_method: str, category: str,
                 major_category: str, purpose_description: str | None = None,
                 payment_method_id: int = 0, category_id: int = 0) -> None:
        self.id = id
        self.purpose = purpose
        self.date = date_val
        self.amount = amount
        self.transaction_type = transaction_type
        self.payment_method = payment_method
        self.payment_method_id = payment_method_id
        self.category = category
        self.category_id = category_id
        self.major_category = major_category
        self.purpose_description = purpose_description

    def get_major_category_display(self) -> str:
        return self._MAJOR_CAT.get(self.major_category, self.major_category)

    def get_transaction_type_display(self) -> str:
        return self._TRANS_TYPE.get(self.transaction_type, self.transaction_type)


class FakeLabel:
    def __init__(self, color: str, id: int = 0, name: str = '') -> None:
        self.id = id
        self.name = name
        self.color = color


class FakeTask:
    def __init__(self, id: int, title: str, label: FakeLabel | None = None) -> None:
        self.id = id
        self.title = title
        self.label = label


class FakeHomeTask:
    def __init__(self, id: int, title: str, start_date: datetime | None,
                 all_day: bool = False, status: str = 'not_started') -> None:
        self.id = id
        self.title = title
        self.start_date = start_date
        self.all_day = all_day
        self.status = status


class FakeMemoType:
    def __init__(self, id: int, name: str, color: str, user: object = None) -> None:
        self.id = id
        self.name = name
        self.color = color
        self.user = user  # None = デフォルト種別、truthy = ユーザー作成


class FakeMemo:
    def __init__(self, id: int, title: str, content: str, updated_date: datetime,
                 is_favorite: bool, memo_type: FakeMemoType) -> None:
        self.id = id
        self.title = title
        self.content = content
        self.updated_date = updated_date
        self.is_favorite = is_favorite
        self.memo_type = memo_type


class FakeShoppingItem:
    _STATUSES = {'insufficient': '不足', 'available': 'あり'}

    def __init__(self, id: int, title: str, price: int | None = None,
                 memo: str | None = None, is_checked: bool = False,
                 remaining_count: int = 0, status: str = 'available') -> None:
        self.id = id
        self.title = title
        self.price = price
        self.memo = memo
        self.is_checked = is_checked
        self.remaining_count = remaining_count
        self.status = status

    def get_status_display(self) -> str:
        return self._STATUSES.get(self.status, self.status)


class FakeCategory:
    def __init__(self, id: int, name: str, chart_color: str = '#4ECDC4') -> None:
        self.id = id
        self.name = name
        self.chart_color = chart_color
        # 設定画面はカテゴリの実効グラフ色を参照する（デモは全て色設定済み）
        self.effective_chart_color = chart_color


class FakePaymentMethod:
    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name


class FakeRecurringPayment:
    _FREQ_DISPLAY = {'daily': '毎日', 'weekly': '毎週', 'monthly': '毎月', 'yearly': '毎年'}
    _TRANS_TYPE = {'income': '収入', 'expense': '支出', 'no_change': '変動なし'}

    def __init__(self, id: int, purpose: str, amount: int, transaction_type: str,
                 category: str, payment_method: str, frequency: str,
                 days_of_week: list[int] | None = None, days_of_month: list[int] | None = None,
                 month_of_year: int | None = None, is_active: bool = True,
                 last_executed: date | None = None) -> None:
        self.id = id
        self.purpose = purpose
        self.amount = amount
        self.transaction_type = transaction_type
        self.category = category
        self.payment_method = payment_method
        self.frequency = frequency
        self.days_of_week = days_of_week or []
        self.days_of_month = days_of_month or []
        self.month_of_year = month_of_year
        self.is_active = is_active
        self.last_executed = last_executed

    def get_frequency_display(self) -> str:
        return self._FREQ_DISPLAY.get(self.frequency, self.frequency)

    def get_transaction_type_display(self) -> str:
        return self._TRANS_TYPE.get(self.transaction_type, self.transaction_type)


class FakeHabitItem:
    def __init__(self, id: int, title: str, frequency: str, color: str,
                 completed: bool, default_coefficient: int,
                 used_coefficient: int, is_positive: bool) -> None:
        self.id = id
        self.title = title
        self.frequency = frequency
        self.color = color
        self.completed = completed
        self.default_coefficient = default_coefficient
        self.used_coefficient = used_coefficient
        self.is_positive = is_positive


class FakeHabitManageItem:
    """習慣管理一覧ページ（habit/list.html）用フェイク。
    frequency は機械値（'daily' 等）で保持し、get_frequency_display() で表示文字を返す。"""
    _FREQ_DISPLAY = {'daily': '毎日', 'weekly': '毎週', 'monthly': '毎月'}

    def __init__(self, id: int, title: str, frequency: str, color: str,
                 is_positive: bool, coefficient: int = 1,
                 weekly_goal: int = 0, monthly_goal: int = 0) -> None:
        self.id = id
        self.title = title
        self.frequency = frequency  # 機械値 'daily' / 'weekly' / 'monthly'
        self.color = color
        self.is_positive = is_positive
        self.coefficient = coefficient
        self.weekly_goal = weekly_goal
        self.monthly_goal = monthly_goal

    def get_frequency_display(self) -> str:
        return self._FREQ_DISPLAY.get(self.frequency, self.frequency)


class FakeWeekHabitRow:
    def __init__(self, id: int, title: str, color: str, days: list[bool],
                 done_count: int, weekly_goal: int, goal_met: bool) -> None:
        self.id = id
        self.title = title
        self.color = color
        self.days = days
        self.done_count = done_count
        self.weekly_goal = weekly_goal
        self.goal_met = goal_met


class FakeWeekHeaderDay:
    def __init__(self, date_str: str, display: str) -> None:
        self.date = date_str
        self.display = display


# ---------------------------------------------------------------------------
# 家計簿デモデータ
# ---------------------------------------------------------------------------

def _demo_expense_transactions() -> list[FakeTransaction]:
    """月次比較を体験できる3か月分の家計簿デモ取引を返す。"""
    rows = [
        (1, '給与', date(2026, 3, 25), 280000, 'income', 3, '銀行振込', 12, '収入', 'variable'),
        (2, 'スーパー（食材）', date(2026, 3, 27), 3240, 'expense', 1, '現金', 1, '食費', 'variable'),
        (3, '電気代', date(2026, 3, 27), 8200, 'expense', 4, '口座振替', 3, '光熱費', 'fixed'),
        (4, '家賃', date(2026, 3, 1), 85000, 'expense', 4, '口座振替', 4, '住居費', 'fixed'),
        (5, 'ランチ', date(2026, 3, 24), 1050, 'expense', 2, 'カード', 2, '外食', 'variable'),
        (6, '書籍', date(2026, 3, 22), 2860, 'expense', 2, 'カード', 5, '教育', 'variable'),
        (7, 'ジム月会費', date(2026, 3, 20), 7700, 'expense', 2, 'カード', 6, '健康', 'fixed'),
        (8, '映画', date(2026, 3, 18), 1800, 'expense', 2, 'カード', 7, '娯楽', 'variable'),
        (9, '水道代', date(2026, 3, 15), 3500, 'expense', 4, '口座振替', 3, '光熱費', 'fixed'),
        (10, 'コンビニ', date(2026, 3, 14), 860, 'expense', 1, '現金', 8, '日用品', 'variable'),
        (11, 'スーパー（日用品）', date(2026, 3, 12), 4320, 'expense', 1, '現金', 8, '日用品', 'variable'),
        (12, '交通費（定期）', date(2026, 3, 10), 9800, 'expense', 2, 'カード', 9, '交通', 'fixed'),
        (13, 'カフェ', date(2026, 3, 9), 680, 'expense', 2, 'カード', 2, '外食', 'variable'),
        (14, 'プレゼント代', date(2026, 3, 5), 16000, 'expense', 2, 'カード', 10, 'ギフト', 'special'),
        (15, '保険料', date(2026, 3, 1), 9710, 'expense', 4, '口座振替', 11, '保険', 'fixed'),
        (16, '給与', date(2026, 2, 25), 280000, 'income', 3, '銀行振込', 12, '収入', 'variable'),
        (17, '家賃', date(2026, 2, 1), 85000, 'expense', 4, '口座振替', 4, '住居費', 'fixed'),
        (18, '食材まとめ買い', date(2026, 2, 8), 28400, 'expense', 1, '現金', 1, '食費', 'variable'),
        (19, '電気代', date(2026, 2, 18), 7600, 'expense', 4, '口座振替', 3, '光熱費', 'fixed'),
        (20, '交通費（定期）', date(2026, 2, 10), 9800, 'expense', 2, 'カード', 9, '交通', 'fixed'),
        (21, '外食', date(2026, 2, 14), 4200, 'expense', 2, 'カード', 2, '外食', 'variable'),
        (22, '給与', date(2026, 1, 25), 275000, 'income', 3, '銀行振込', 12, '収入', 'variable'),
        (23, '家賃', date(2026, 1, 1), 85000, 'expense', 4, '口座振替', 4, '住居費', 'fixed'),
        (24, '食費', date(2026, 1, 12), 31500, 'expense', 1, '現金', 1, '食費', 'variable'),
        (25, '帰省交通費', date(2026, 1, 4), 22000, 'expense', 2, 'カード', 9, '交通', 'special'),
        (26, '光熱費', date(2026, 1, 18), 12400, 'expense', 4, '口座振替', 3, '光熱費', 'fixed'),
    ]
    return [
        FakeTransaction(
            row[0], row[1], row[2], row[3], row[4], row[6], row[8], row[9],
            payment_method_id=row[5], category_id=row[7],
        )
        for row in rows
    ]


def _demo_expense_summary(transactions: list[FakeTransaction]) -> tuple[float, float, float]:
    income = float(sum(item.amount for item in transactions if item.transaction_type == 'income'))
    expense = float(sum(item.amount for item in transactions if item.transaction_type == 'expense'))
    return income, expense, income - expense


def _demo_selected_ids(query: QueryDict, name: str) -> list[int]:
    selected: list[int] = []
    for raw_value in query.getlist(name):
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            continue
        if value > 0 and value not in selected:
            selected.append(value)
    return selected


def _demo_category_chart_data(
    transactions: list[FakeTransaction],
    categories: list[FakeCategory],
) -> str:
    totals: dict[int, float] = {}
    for item in transactions:
        if item.transaction_type == 'expense':
            totals[item.category_id] = totals.get(item.category_id, 0.0) + item.amount
    category_map = {item.id: item for item in categories}
    rows = sorted(totals.items(), key=lambda row: row[1], reverse=True)
    if not rows:
        return json.dumps({
            'labels': ['データなし'],
            'filterValues': [''],
            'datasets': [{'data': [1], 'backgroundColor': [CHART_COLORS['no_data']]}],
        })
    top_rows = rows[:5]
    other_total = sum(amount for _, amount in rows[5:])
    labels = [category_map[category_id].name for category_id, _ in top_rows]
    amounts = [amount for _, amount in top_rows]
    colors = [category_map[category_id].chart_color for category_id, _ in top_rows]
    filter_values = [str(category_id) for category_id, _ in top_rows]
    if other_total:
        labels.append('その他')
        amounts.append(other_total)
        colors.append(CHART_COLORS['no_data'])
        filter_values.append(f"exclude:{','.join(str(row[0]) for row in top_rows)}")
    return json.dumps({
        'labels': labels,
        'filterValues': filter_values,
        'datasets': [{'data': amounts, 'backgroundColor': colors}],
    })


def _demo_major_category_chart_data(transactions: list[FakeTransaction]) -> str:
    totals: dict[str, float] = {}
    for item in transactions:
        if item.transaction_type == 'expense':
            totals[item.major_category] = totals.get(item.major_category, 0.0) + item.amount
    rows = sorted(totals.items(), key=lambda row: row[1], reverse=True)
    if not rows:
        return json.dumps({
            'labels': ['データなし'],
            'filterValues': [''],
            'datasets': [{'data': [1], 'backgroundColor': [CHART_COLORS['no_data']]}],
        })
    return json.dumps({
        'labels': [MAJOR_CATEGORY_LABELS[key] for key, _ in rows],
        'filterValues': [key for key, _ in rows],
        'datasets': [{
            'data': [amount for _, amount in rows],
            'backgroundColor': [CHART_COLORS['major_category'][key] for key, _ in rows],
        }],
    })


def _demo_daily_chart_data(
    transactions: list[FakeTransaction],
    year: int,
    month: int,
) -> tuple[str, str]:
    day_count = cal_module.monthrange(year, month)[1]
    labels = [date(year, month, day).isoformat() for day in range(1, day_count + 1)]
    expense_values: list[float] = []
    balance_values: list[float] = []
    balance = 0.0
    for label in labels:
        day = date.fromisoformat(label)
        day_transactions = [item for item in transactions if item.date == day]
        income, expense, _ = _demo_expense_summary(day_transactions)
        balance += income - expense
        expense_values.append(expense)
        balance_values.append(balance)
    return json.dumps({
        'labels': labels,
        'datasets': [{'label': '支出', 'data': expense_values, 'backgroundColor': CHART_COLORS['expense_bar']}],
    }), json.dumps({
        'labels': labels,
        'datasets': [{'label': '収支', 'data': balance_values, 'fill': False, 'borderColor': CHART_COLORS['balance_line']}],
    })


def _demo_monthly_chart_data(transactions: list[FakeTransaction]) -> str:
    income_values: list[float] = []
    expense_values: list[float] = []
    for month in range(1, 13):
        monthly = [item for item in transactions if item.date.month == month]
        income, expense, _ = _demo_expense_summary(monthly)
        income_values.append(income)
        expense_values.append(expense)
    return json.dumps({
        'labels': [f'{month}月' for month in range(1, 13)],
        'datasets': [
            {'label': '収入', 'data': income_values, 'backgroundColor': 'rgba(54, 162, 235, 0.7)'},
            {'label': '支出', 'data': expense_values, 'backgroundColor': CHART_COLORS['expense_bar']},
        ],
    })


def get_expenses_context(params: QueryDict | None = None) -> dict:
    """実画面と同じ検索・表示切替を適用した家計簿デモコンテキストを返す。"""
    query = params if params is not None else QueryDict('')
    transactions = _demo_expense_transactions()
    categories = [
        FakeCategory(index, name, CHART_COLORS['category'][index % len(CHART_COLORS['category'])])
        for index, name in enumerate(
            ['食費', '外食', '光熱費', '住居費', '教育', '健康', '娯楽', '日用品', '交通', 'ギフト', '保険', '収入'],
            start=1,
        )
    ]
    payment_methods = [
        FakePaymentMethod(1, '現金'), FakePaymentMethod(2, 'カード'),
        FakePaymentMethod(3, '銀行振込'), FakePaymentMethod(4, '口座振替'),
    ]

    search_query = query.get('search', '').strip()
    filter_transaction_type = query.get('transaction_type', '')
    filter_major_category = query.get('major_category', '')
    filter_categories = _demo_selected_ids(query, 'category')
    excluded_categories = _demo_selected_ids(query, 'exclude_category')
    filter_payment_methods = _demo_selected_ids(query, 'payment_method')
    excluded_payment_methods = _demo_selected_ids(query, 'exclude_payment_method')
    try:
        filter_date = date.fromisoformat(query.get('date', '')).isoformat()
    except (TypeError, ValueError):
        filter_date = ''

    def apply_filters(
        items: list[FakeTransaction],
        *,
        include_exact_date: bool = True,
    ) -> list[FakeTransaction]:
        filtered = list(items)
        if search_query:
            needle = search_query.lower()
            filtered = [
                item for item in filtered
                if needle in item.purpose.lower()
                or needle in (item.purpose_description or '').lower()
                or needle in item.category.lower()
                or needle in item.payment_method.lower()
            ]
        if filter_transaction_type:
            filtered = [item for item in filtered if item.transaction_type == filter_transaction_type]
        if filter_major_category:
            filtered = [item for item in filtered if item.major_category == filter_major_category]
        if filter_categories:
            filtered = [item for item in filtered if item.category_id in filter_categories]
        if excluded_categories:
            filtered = [item for item in filtered if item.category_id not in excluded_categories]
        if filter_payment_methods:
            filtered = [item for item in filtered if item.payment_method_id in filter_payment_methods]
        if excluded_payment_methods:
            filtered = [item for item in filtered if item.payment_method_id not in excluded_payment_methods]
        if include_exact_date and filter_date:
            filtered = [item for item in filtered if item.date.isoformat() == filter_date]
        return filtered

    view_mode = 'year' if query.get('view_mode') == 'year' else 'month'
    if view_mode == 'year':
        try:
            current_year = int(query.get('target_date', '2026'))
        except (TypeError, ValueError):
            current_year = 2026
        period_transactions = [item for item in transactions if item.date.year == current_year]
        filtered_transactions = apply_filters(period_transactions)
        default_target_date = str(current_year)
        target_month = f'{current_year}年'
        monthly_chart_data_json = _demo_monthly_chart_data(filtered_transactions)
        year_range = list(range(current_year - 5, current_year + 3))
        year_for_toggle = current_year
        month_for_toggle = f'{current_year}-03'
    else:
        try:
            target_date = datetime.strptime(query.get('target_date', '2026-03'), '%Y-%m').date()
        except (TypeError, ValueError):
            target_date = date(2026, 3, 1)
        current_year = target_date.year
        current_month = target_date.month
        period_transactions = [
            item for item in transactions
            if item.date.year == current_year and item.date.month == current_month
        ]
        filtered_transactions = apply_filters(period_transactions)
        default_target_date = f'{current_year:04d}-{current_month:02d}'
        target_month = f'{current_year}年{current_month:02d}月'
        year_for_toggle = current_year
        month_for_toggle = default_target_date

    sort_by = query.get('sort_by', 'date_desc')
    if sort_by == 'date_asc':
        filtered_transactions.sort(key=lambda item: (item.date, item.id))
    elif sort_by == 'amount_desc':
        filtered_transactions.sort(key=lambda item: (item.amount, item.date), reverse=True)
    elif sort_by == 'amount_asc':
        filtered_transactions.sort(key=lambda item: (item.amount, item.date))
    else:
        sort_by = 'date_desc'
        filtered_transactions.sort(key=lambda item: (item.date, item.id), reverse=True)

    per_page_options = ['10', '20', '50', '100']
    per_page_raw = query.get('per_page', '20')
    per_page = int(per_page_raw) if per_page_raw in per_page_options else 20
    paginator = Paginator(filtered_transactions, per_page)
    transactions_page = paginator.get_page(query.get('page'))
    total_income, total_expense, net_balance = _demo_expense_summary(filtered_transactions)
    pagination_query = query.copy()
    pagination_query.pop('page', None)
    has_active_filters = bool(
        search_query or filter_transaction_type or filter_major_category
        or filter_categories or excluded_categories or filter_payment_methods
        or excluded_payment_methods or filter_date
    )

    context = {
        'view_mode': view_mode,
        'transactions_page': transactions_page,
        'transactions_count': len(filtered_transactions),
        'total_income': total_income,
        'total_expense': total_expense,
        'net_balance': net_balance,
        'total_income_formatted': f'{total_income:,.0f}',
        'total_expense_formatted': f'{total_expense:,.0f}',
        'net_balance_formatted': f'{net_balance:,.0f}',
        'target_month': target_month,
        'search_query': search_query,
        'user_categories': categories,
        'user_payment_methods': payment_methods,
        'filter_transaction_type': filter_transaction_type,
        'filter_major_category': filter_major_category,
        'filter_category': str(filter_categories[0]) if len(filter_categories) == 1 else '',
        'filter_payment_method': str(filter_payment_methods[0]) if len(filter_payment_methods) == 1 else '',
        'filter_categories': filter_categories,
        'excluded_categories': excluded_categories,
        'filter_payment_methods': filter_payment_methods,
        'excluded_payment_methods': excluded_payment_methods,
        'filter_date': filter_date,
        'has_active_filters': has_active_filters,
        'pagination_query': pagination_query.urlencode(),
        'default_target_date': default_target_date,
        'per_page': per_page,
        'per_page_options': per_page_options,
        'sort_by': sort_by,
        'year_for_toggle': year_for_toggle,
        'month_for_toggle': month_for_toggle,
    }
    if view_mode == 'year':
        context.update({
            'current_year': current_year,
            'year_range': year_range,
            'monthly_chart_data_json': monthly_chart_data_json,
        })
        return context

    category_data_json = _demo_category_chart_data(filtered_transactions, categories)
    major_category_data_json = _demo_major_category_chart_data(filtered_transactions)
    expense_data_json, balance_data_json = _demo_daily_chart_data(
        filtered_transactions,
        current_year,
        current_month,
    )
    comparison_transactions = apply_filters(transactions, include_exact_date=False)
    current_comparison = [
        item for item in comparison_transactions
        if item.date.year == current_year and item.date.month == current_month
    ]
    previous_target = date(current_year, current_month, 1) - timedelta(days=1)
    previous_comparison = [
        item for item in comparison_transactions
        if item.date.year == previous_target.year and item.date.month == previous_target.month
    ]
    average_month_count = len({(item.date.year, item.date.month) for item in comparison_transactions})
    current_summary = _demo_expense_summary(current_comparison)
    previous_summary = _demo_expense_summary(previous_comparison)
    all_summary = _demo_expense_summary(comparison_transactions)
    divisor = average_month_count or 1
    comparison_data_json = json.dumps({
        'labels': [
            f'{current_year}年{current_month}月',
            f'{previous_target.year}年{previous_target.month}月',
            '全期間平均',
        ],
        'datasets': [
            {'label': '収入', 'data': [current_summary[0], previous_summary[0], all_summary[0] / divisor], 'backgroundColor': 'rgba(54, 162, 235, 0.7)'},
            {'label': '支出', 'data': [current_summary[1], previous_summary[1], all_summary[1] / divisor], 'backgroundColor': CHART_COLORS['expense_bar']},
            {'label': '収支', 'data': [current_summary[2], previous_summary[2], all_summary[2] / divisor], 'backgroundColor': 'rgba(40, 167, 69, 0.7)'},
        ],
    })
    context.update({
        'category_data_json': category_data_json,
        'major_category_data_json': major_category_data_json,
        'expense_data_json': expense_data_json,
        'balance_data_json': balance_data_json,
        'comparison_data_json': comparison_data_json,
        'comparison_average_month_count': average_month_count,
    })
    return context


# ---------------------------------------------------------------------------
# タスク管理デモデータ
# ---------------------------------------------------------------------------

# カレンダー・日別タスク共通ラベル定義
_LW = FakeLabel('#e83e8c', 1, '仕事')
_LH = FakeLabel('#20c997', 2, '健康')
_LS = FakeLabel('#fd7e14', 3, '勉強')
_LP = FakeLabel('#6f42c1', 4, 'プライベート')

# day/<date>/ API で使うデモタスクマップ（キー: YYYY-MM-DD）
_DEMO_DAY_TASKS: dict[str, list[dict]] = {
    '2026-03-03': [{'id': 1,  'title': '月次報告書作成',      'status': 'done',        'priority': 'high',   'label': {'color': _LW.color, 'name': _LW.name}, 'due_date': '2026-03-03', 'description': None, 'priority_display': '高', 'status_display': '完了'}],
    '2026-03-05': [{'id': 2,  'title': '歯医者',              'status': 'done',        'priority': 'medium', 'label': {'color': _LP.color, 'name': _LP.name}, 'due_date': '2026-03-05', 'description': None, 'priority_display': '中', 'status_display': '完了'}],
    '2026-03-09': [
        {'id': 3,  'title': 'チームミーティング',              'status': 'done',        'priority': 'high',   'label': {'color': _LW.color, 'name': _LW.name}, 'due_date': '2026-03-09', 'description': None, 'priority_display': '高', 'status_display': '完了'},
        {'id': 4,  'title': '読書',                           'status': 'done',        'priority': 'low',    'label': {'color': _LS.color, 'name': _LS.name}, 'due_date': '2026-03-09', 'description': None, 'priority_display': '低', 'status_display': '完了'},
    ],
    '2026-03-10': [{'id': 5,  'title': 'ジム',                'status': 'done',        'priority': 'medium', 'label': {'color': _LH.color, 'name': _LH.name}, 'due_date': '2026-03-10', 'description': None, 'priority_display': '中', 'status_display': '完了'}],
    '2026-03-12': [{'id': 6,  'title': '企画書提出',          'status': 'done',        'priority': 'high',   'label': {'color': _LW.color, 'name': _LW.name}, 'due_date': '2026-03-12', 'description': None, 'priority_display': '高', 'status_display': '完了'}],
    '2026-03-15': [
        {'id': 7,  'title': '散歩',                           'status': 'done',        'priority': 'low',    'label': {'color': _LH.color, 'name': _LH.name}, 'due_date': '2026-03-15', 'description': None, 'priority_display': '低', 'status_display': '完了'},
        {'id': 8,  'title': 'Python学習',                    'status': 'done',        'priority': 'medium', 'label': {'color': _LS.color, 'name': _LS.name}, 'due_date': '2026-03-15', 'description': None, 'priority_display': '中', 'status_display': '完了'},
    ],
    '2026-03-17': [{'id': 9,  'title': '友人と食事',          'status': 'done',        'priority': 'medium', 'label': {'color': _LP.color, 'name': _LP.name}, 'due_date': '2026-03-17', 'description': None, 'priority_display': '中', 'status_display': '完了'}],
    '2026-03-19': [{'id': 10, 'title': 'コードレビュー',      'status': 'done',        'priority': 'high',   'label': {'color': _LW.color, 'name': _LW.name}, 'due_date': '2026-03-19', 'description': None, 'priority_display': '高', 'status_display': '完了'}],
    '2026-03-20': [{'id': 11, 'title': 'ジム',                'status': 'done',        'priority': 'medium', 'label': {'color': _LH.color, 'name': _LH.name}, 'due_date': '2026-03-20', 'description': None, 'priority_display': '中', 'status_display': '完了'}],
    '2026-03-23': [
        {'id': 12, 'title': '週次振り返り',                   'status': 'done',        'priority': 'medium', 'label': {'color': _LW.color, 'name': _LW.name}, 'due_date': '2026-03-23', 'description': None, 'priority_display': '中', 'status_display': '完了'},
        {'id': 13, 'title': '読書',                           'status': 'done',        'priority': 'low',    'label': {'color': _LS.color, 'name': _LS.name}, 'due_date': '2026-03-23', 'description': None, 'priority_display': '低', 'status_display': '完了'},
    ],
    '2026-03-24': [{'id': 14, 'title': 'オンライン勉強会',    'status': 'done',        'priority': 'medium', 'label': {'color': _LS.color, 'name': _LS.name}, 'due_date': '2026-03-24', 'description': None, 'priority_display': '中', 'status_display': '完了'}],
    '2026-03-26': [{'id': 15, 'title': 'チームランチ',        'status': 'done',        'priority': 'low',    'label': {'color': _LW.color, 'name': _LW.name}, 'due_date': '2026-03-26', 'description': None, 'priority_display': '低', 'status_display': '完了'}],
    '2026-03-27': [
        {'id': 16, 'title': '週次レポート作成',               'status': 'in_progress', 'priority': 'high',   'label': {'color': _LW.color, 'name': _LW.name}, 'due_date': '2026-03-27', 'description': '今週の進捗をまとめる', 'priority_display': '高', 'status_display': '進行中'},
        {'id': 17, 'title': '歯医者の予約確認',              'status': 'todo',        'priority': 'medium', 'label': None, 'due_date': '2026-03-27', 'description': None, 'priority_display': '中', 'status_display': '未了'},
        {'id': 18, 'title': 'メール返信',                    'status': 'todo',        'priority': 'low',    'label': None, 'due_date': '2026-03-27', 'description': None, 'priority_display': '低', 'status_display': '未了'},
    ],
    '2026-03-28': [{'id': 19, 'title': '企画書最終確認',      'status': 'todo',        'priority': 'high',   'label': {'color': _LW.color, 'name': _LW.name}, 'due_date': '2026-03-28', 'description': None, 'priority_display': '高', 'status_display': '未了'}],
    '2026-03-30': [{'id': 20, 'title': 'ジム',                'status': 'todo',        'priority': 'low',    'label': {'color': _LH.color, 'name': _LH.name}, 'due_date': '2026-03-30', 'description': None, 'priority_display': '低', 'status_display': '未了'}],
}


def get_demo_day_tasks_json() -> str:
    return json.dumps(_DEMO_DAY_TASKS)


def get_tasks_context() -> dict:
    year, month = 2026, 3
    today = date(2026, 3, 27)

    lw = _LW
    lh = _LH
    ls = _LS
    lp = _LP

    fake_tasks: dict[int, list[FakeTask]] = {
        3:  [FakeTask(1,  '月次報告書作成', lw)],
        5:  [FakeTask(2,  '歯医者', lp)],
        9:  [FakeTask(3,  'チームミーティング', lw), FakeTask(4, '読書', ls)],
        10: [FakeTask(5,  'ジム', lh)],
        12: [FakeTask(6,  '企画書提出', lw)],
        15: [FakeTask(7,  '散歩', lh), FakeTask(8, 'Python学習', ls)],
        17: [FakeTask(9,  '友人と食事', lp)],
        19: [FakeTask(10, 'コードレビュー', lw)],
        20: [FakeTask(11, 'ジム', lh)],
        23: [FakeTask(12, '週次振り返り', lw), FakeTask(13, '読書', ls)],
        24: [FakeTask(14, 'オンライン勉強会', ls)],
        26: [FakeTask(15, 'チームランチ', lw)],
        27: [FakeTask(16, '週次レポート作成', lw), FakeTask(17, '歯医者の予約確認', None), FakeTask(18, 'メール返信', None)],
        28: [FakeTask(19, '企画書最終確認', lw)],
        30: [FakeTask(20, 'ジム', lh)],
    }

    # 日曜始まりカレンダー
    cal = cal_module.Calendar(firstweekday=6)
    month_calendar = cal.monthdatescalendar(year, month)
    weekday_labels = ['日', '月', '火', '水', '木', '金', '土']

    calendar_data = []
    for week in month_calendar:
        week_data = []
        for d in week:
            is_current = (d.month == month)
            day_tasks = fake_tasks.get(d.day, []) if is_current else []
            week_data.append({
                'day': d.day, 'month': d.month, 'year': d.year,
                'tasks': day_tasks, 'task_count': len(day_tasks),
                'is_current_month': is_current, 'is_today': (d == today),
            })
        calendar_data.append(week_data)

    return {
        'view_mode':          'month',
        'target_month':       '2026年3月',
        'default_target_date':'2026-03',
        'calendar_data':      calendar_data,
        'weekday_labels':     weekday_labels,
        'week_start':         'sunday',
    }


# ---------------------------------------------------------------------------
# 習慣トラッカーデモデータ
# ---------------------------------------------------------------------------

def get_habits_context() -> dict:
    today = date(2026, 3, 27)

    today_status = [
        FakeHabitItem(1, '朝のランニング',      '毎日',  '#28a745', True,  5, 5, True),
        FakeHabitItem(2, '読書30分',            '毎日',  '#28a745', True,  3, 3, True),
        FakeHabitItem(3, '筋トレ',              '週3回', '#28a745', False, 8, 8, True),
        FakeHabitItem(4, 'スマホ使用2時間以内', '毎日',  '#dc3545', False, 4, 4, False),
        FakeHabitItem(5, 'お菓子を食べない',    '毎日',  '#dc3545', True,  6, 6, False),
    ]

    weekday_names = ['月', '火', '水', '木', '金', '土', '日']
    week_start_date = date(2026, 3, 23)
    week_header_data = [
        FakeWeekHeaderDay(
            (week_start_date + timedelta(days=i)).isoformat(),
            f"{weekday_names[i]}\n{(week_start_date + timedelta(days=i)).day}",
        )
        for i in range(7)
    ]

    week_data = [
        FakeWeekHabitRow(1, '朝のランニング',      '#28a745', [True, True, True, False, True, True, True], 6, 7, False),
        FakeWeekHabitRow(2, '読書30分',            '#28a745', [True, False, True, True, True, False, True], 5, 5, True),
        FakeWeekHabitRow(3, '筋トレ',              '#28a745', [True, False, True, False, False, False, False], 2, 3, False),
        FakeWeekHabitRow(4, 'スマホ使用2時間以内', '#dc3545', [True, True, False, True, False, False, False], 3, 7, False),
        FakeWeekHabitRow(5, 'お菓子を食べない',    '#dc3545', [True, True, True, False, True, True, True], 6, 7, False),
    ]

    # ヒートマップ用のフェイク達成データ（過去1年分、決定的なパターン）
    heatmap_data: dict[str, int] = {}
    heatmap_start = today - timedelta(days=364)
    for i in range(365):
        day = heatmap_start + timedelta(days=i)
        count = (i * 7 + day.day) % 6  # 0〜5件の達成数を決定的に散らす
        if count:
            heatmap_data[day.isoformat()] = count

    return {
        'selected_date':  today.isoformat(),
        'min_date':       '2025-01-01',
        'today':          today.isoformat(),
        'today_status':   today_status,
        'week_header_data': week_header_data,
        'week_data':      week_data,
        'selected_year':  None,
        'year_choices':   [2025, 2026],
        'heatmap_data_json': json.dumps(heatmap_data),
    }


# ---------------------------------------------------------------------------
# メモデモデータ
# ---------------------------------------------------------------------------

def get_memos_context() -> dict:
    type_work    = FakeMemoType(1, '仕事',         '#6f42c1')
    type_idea    = FakeMemoType(2, 'アイデア',     '#20c997')
    type_study   = FakeMemoType(3, '学習',         '#fd7e14')
    type_private = FakeMemoType(4, 'プライベート', '#e83e8c')

    memos = [
        FakeMemo(1, 'Q1振り返りと次期目標',
                 '- 売上目標：達成率108%\n- 次期はマーケット拡大に注力\n- 重点課題：カスタマーサクセス強化',
                 datetime(2026, 3, 26, 16, 20), True, type_work),
        FakeMemo(2, '新しいルーティンのアイデア',
                 '朝6時起床 → ストレッチ10分 → ランニング30分 → シャワー → 読書30分 → 朝食\n\nこのルーティンを1ヶ月続けてみる',
                 datetime(2026, 3, 24,  9,  0), False, type_idea),
        FakeMemo(3, 'Python学習メモ',
                 '## デコレータ\n`@property` を使うと getter/setter をシンプルに書ける\n\n```python\nclass Circle:\n    @property\n    def area(self):\n        return 3.14 * self.r ** 2\n```',
                 datetime(2026, 3, 20, 22, 15), False, type_study),
        FakeMemo(4, '旅行計画（京都・大阪）',
                 '4月上旬予定。新幹線は早割で購入済み。\nホテルは要予約。\n\n行きたい場所:\n- 伏見稲荷大社\n- 嵐山\n- 道頓堀',
                 datetime(2026, 3, 15, 18, 45), True, type_private),
        FakeMemo(5, 'プロジェクトX メモ',
                 '要件定義 完了\nUI設計 進行中\nバックエンド開発 未着手\n\n納期: 5月末',
                 datetime(2026, 3, 10, 10,  0), False, type_work),
        FakeMemo(6, 'おすすめ本リスト',
                 '- アトミック・ハビッツ（ジェームズ・クリアー）\n- ファクトフルネス（ハンス・ロスリング）\n- エッセンシャル思考（グレッグ・マキューン）',
                 datetime(2026, 3,  8, 20,  0), False, type_study),
    ]

    paginator = Paginator(memos, 20)
    page_obj = paginator.get_page(1)

    return {
        'page_obj':        page_obj,
        'search_query':    '',
        'memo_type_filter':'',
        'favorite_filter': '',
        'memo_type_choices': [type_work, type_idea, type_study, type_private],
        'per_page':        20,
        'per_page_options':['10', '20', '50', '100'],
    }


# ---------------------------------------------------------------------------
# 買い物リストデモデータ
# ---------------------------------------------------------------------------

def get_shopping_context() -> dict:
    one_time_items = [
        FakeShoppingItem(1, 'ケーキ（誕生日用）', None,  '3月28日 誕生日', False),
        FakeShoppingItem(2, '電池（単3×4本）',    None,  None,            False),
        FakeShoppingItem(3, 'ノート（A5）',        350,   None,            True),
        FakeShoppingItem(4, '傘',                  1500,  None,            False),
    ]
    recurring_items = [
        FakeShoppingItem(5,  '牛乳',                    None,  None, False, 0, 'insufficient'),
        FakeShoppingItem(6,  '卵（10個入り）',           228,   None, False, 1, 'insufficient'),
        FakeShoppingItem(7,  'シャンプー',               None,  None, False, 1, 'insufficient'),
        FakeShoppingItem(8,  '米（5kg）',                2500,  None, False, 3, 'available'),
        FakeShoppingItem(9,  '洗剤（液体）',             380,   None, False, 2, 'available'),
        FakeShoppingItem(10, 'トイレットペーパー（12ロール）', 698, None, False, 4, 'available'),
    ]

    return {
        'one_time_items':     one_time_items,
        'recurring_items':    recurring_items,
        'has_checked_one_time': True,
        'search_query':       '',
    }


# ---------------------------------------------------------------------------
# 各画面向け API レスポンス用フェイク JSON（JS の fetch 差し替えに使用）
# ---------------------------------------------------------------------------

def get_demo_habit_status_json() -> str:
    status = [
        {'id': 1, 'title': '朝のランニング',      'frequency': '毎日',  'coefficient': 5,  'default_coefficient': 5,  'used_coefficient': 5,  'color': '#28a745', 'is_positive': True,  'completed': True},
        {'id': 2, 'title': '読書30分',            'frequency': '毎日',  'coefficient': 3,  'default_coefficient': 3,  'used_coefficient': 3,  'color': '#28a745', 'is_positive': True,  'completed': True},
        {'id': 3, 'title': '筋トレ',              'frequency': '週3回', 'coefficient': 8,  'default_coefficient': 8,  'used_coefficient': 8,  'color': '#28a745', 'is_positive': True,  'completed': False},
        {'id': 4, 'title': 'スマホ使用2時間以内', 'frequency': '毎日',  'coefficient': -4, 'default_coefficient': 4,  'used_coefficient': 4,  'color': '#dc3545', 'is_positive': False, 'completed': False},
        {'id': 5, 'title': 'お菓子を食べない',    'frequency': '毎日',  'coefficient': -6, 'default_coefficient': 6,  'used_coefficient': 6,  'color': '#dc3545', 'is_positive': False, 'completed': True},
    ]
    return json.dumps({'status': status, 'date': '2026-03-27'})


def get_demo_heatmap_json() -> str:
    pattern = [5, 3, 4, 5, 5, 0, 0, 4, 3, 5, 4, 5, 0, 0, 5, 4, 3, 5, 4, 5, 0, 0, 3, 5, 4, 3, 5, 5, 0, 0]
    base = date(2025, 4, 1)
    end = date(2026, 3, 27)
    data = {}
    idx = 0
    d = base
    while d <= end:
        score = pattern[idx % len(pattern)]
        if score > 0:
            data[d.isoformat()] = float(score)
        d += timedelta(days=1)
        idx += 1
    return json.dumps(data)


def get_demo_board_sets_json() -> str:
    return json.dumps({'sets': [{'id': 1, 'name': 'デフォルト', 'order': 0}]})


def get_expenses_settings_context() -> dict:
    payments = [
        FakePaymentMethod(1, '現金'),
        FakePaymentMethod(2, 'カード'),
        FakePaymentMethod(3, '銀行振込'),
        FakePaymentMethod(4, '口座振替'),
    ]
    purposes = [
        FakeCategory(1,  '食費',   '#4e79a7'),
        FakeCategory(2,  '外食',   '#f28e2b'),
        FakeCategory(3,  '光熱費', '#e15759'),
        FakeCategory(4,  '住居費', '#76b7b2'),
        FakeCategory(5,  '教育',   '#59a14f'),
        FakeCategory(6,  '健康',   '#edc948'),
        FakeCategory(7,  '娯楽',   '#b07aa1'),
        FakeCategory(8,  '日用品', '#ff9da7'),
        FakeCategory(9,  '交通',   '#9c755f'),
        FakeCategory(10, 'ギフト', '#bab0ac'),
        FakeCategory(11, '保険',   '#86bcb6'),
        FakeCategory(12, '収入',   '#76b7b2'),
    ]

    class _FakeForm:
        """フォームエラー表示用の最小フェイク"""
        non_field_errors_list: list = []
        errors: dict = {}

        def non_field_errors(self) -> list:
            return self.non_field_errors_list

    return {
        'payments': payments,
        'purposes': purposes,
        'payment_form': _FakeForm(),
        'purpose_form': _FakeForm(),
    }


class FakeExternalCalendar:
    """外部カレンダー（ICS購読）のフェイク"""

    def __init__(self, id: int, name: str, color: str, last_error: str = '') -> None:
        self.id = id
        self.name = name
        self.color = color
        self.last_synced_at = datetime.now() - timedelta(minutes=12)
        self.last_error = last_error


def get_task_settings_context() -> dict:
    calendar_feed_url = 'https://carbohydratepro.com/calendar/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.ics'
    labels = [
        FakeLabel('#e83e8c', 1, '仕事'),
        FakeLabel('#20c997', 2, '健康'),
        FakeLabel('#fd7e14', 3, '勉強'),
        FakeLabel('#6f42c1', 4, 'プライベート'),
    ]
    external_calendars = [
        FakeExternalCalendar(1, 'Googleカレンダー', '#4285f4'),
        FakeExternalCalendar(2, '家族の予定', '#20c997'),
    ]
    return {
        'labels': labels,
        'current_week_start': 'sunday',
        'calendar_feed_url': calendar_feed_url,
        'external_calendars': external_calendars,
    }


def get_memo_settings_context() -> dict:
    _sentinel = object()  # truthy な非None値（ユーザー作成を示す）
    memo_types = [
        FakeMemoType(0, 'その他',       '#6c757d', user=None),
        FakeMemoType(1, '仕事',         '#6f42c1', user=_sentinel),
        FakeMemoType(2, 'アイデア',     '#20c997', user=_sentinel),
        FakeMemoType(3, '学習',         '#fd7e14', user=_sentinel),
        FakeMemoType(4, 'プライベート', '#e83e8c', user=_sentinel),
    ]
    return {
        'memo_types': memo_types,
        'form': None,
    }


def get_habit_list_context() -> dict:
    habits = [
        FakeHabitManageItem(1, '朝のランニング',      'daily',   '#28a745', True,  5, 0, 0),
        FakeHabitManageItem(2, '読書30分',            'daily',   '#28a745', True,  3, 0, 0),
        FakeHabitManageItem(3, '筋トレ',              'weekly',  '#28a745', True,  8, 3, 0),
        FakeHabitManageItem(4, 'スマホ使用2時間以内', 'daily',   '#dc3545', False, 4, 0, 0),
        FakeHabitManageItem(5, 'お菓子を食べない',    'daily',   '#dc3545', False, 6, 0, 0),
    ]
    return {
        'habits': habits,
        'form': None,
    }


def get_demo_board_tasks_json() -> str:
    tasks = [
        {'id': 1, 'title': '資料のPDF化',              'status': 'todo',  'order': 0},
        {'id': 2, 'title': 'ミーティング議事録まとめ', 'status': 'todo',  'order': 1},
        {'id': 3, 'title': '競合調査',                 'status': 'todo',  'order': 2},
        {'id': 4, 'title': 'ランディングページの修正', 'status': 'doing', 'order': 0},
        {'id': 5, 'title': 'バグ調査 #142',            'status': 'doing', 'order': 1},
        {'id': 6, 'title': '週次レポート送付',         'status': 'done',  'order': 0},
        {'id': 7, 'title': 'デプロイ手順書の更新',     'status': 'done',  'order': 1},
        {'id': 8, 'title': 'コードレビュー #88',       'status': 'done',  'order': 2},
        {'id': 9, 'title': 'テストケース追加',         'status': 'done',  'order': 3},
    ]
    return json.dumps({'tasks': tasks})


# ---------------------------------------------------------------------------
# 定期支払いデモデータ
# ---------------------------------------------------------------------------

def get_recurring_payments_context() -> dict:
    recurring_payments = [
        FakeRecurringPayment(1, '家賃', 85000, 'expense', '住居費', '口座振替',
                             'monthly', days_of_month=[1], is_active=True,
                             last_executed=date(2026, 3, 1)),
        FakeRecurringPayment(2, 'ジム月会費', 7700, 'expense', '健康', 'カード',
                             'monthly', days_of_month=[20], is_active=True,
                             last_executed=date(2026, 3, 20)),
        FakeRecurringPayment(3, '保険料', 9710, 'expense', '保険', '口座振替',
                             'monthly', days_of_month=[1], is_active=True,
                             last_executed=date(2026, 3, 1)),
        FakeRecurringPayment(4, '交通費（定期）', 9800, 'expense', '交通', 'カード',
                             'monthly', days_of_month=[10], is_active=True,
                             last_executed=date(2026, 3, 10)),
        FakeRecurringPayment(5, 'サブスクA', 980, 'expense', '娯楽', 'カード',
                             'monthly', days_of_month=[5], is_active=False,
                             last_executed=date(2026, 2, 5)),
        FakeRecurringPayment(6, '給与', 280000, 'income', '収入', '銀行振込',
                             'monthly', days_of_month=[25], is_active=True,
                             last_executed=date(2026, 3, 25)),
    ]
    return {'recurring_payments': recurring_payments}


# ---------------------------------------------------------------------------
# ホーム（統合ダッシュボード）デモデータ
# ---------------------------------------------------------------------------

def _demo_budget_row(category, limit: int, used: int, has_budget: bool = True) -> dict:
    """予算画面/ダッシュボード用のフェイク予算行（build_budget_overview と同形）を返す。"""
    percent = round(used / limit * 100, 1) if limit > 0 else 0.0
    status = 'over' if percent > 100 else ('warning' if percent >= 80 else 'ok')
    return {
        'category': category,
        'has_budget': has_budget,
        'limit': limit,
        'used': used,
        'remaining': limit - used,
        'percent': percent,
        'percent_bar': min(percent, 100.0),
        'status': status,
    }


def _demo_budget_overview() -> dict:
    """デモ用の予算消化サマリー。"""
    rows = [
        _demo_budget_row(FakeCategory(1, '食費', '#4e79a7'), 40000, 33000),
        _demo_budget_row(FakeCategory(2, '外食', '#f28e2b'), 15000, 18200),
        _demo_budget_row(FakeCategory(3, '光熱費', '#e15759'), 20000, 12800),
        _demo_budget_row(FakeCategory(8, '日用品', '#ff9da7'), 10000, 4200),
        _demo_budget_row(FakeCategory(7, '娯楽', '#b07aa1'), 0, 6500, has_budget=False),
    ]
    overall = _demo_budget_row(FakeCategory(0, '全体', ''), 150000, 132450)
    over_count = sum(1 for r in rows if r['has_budget'] and r['status'] == 'over')
    return {'overall': overall, 'category_rows': rows, 'over_count': over_count, 'has_any_budget': True}


def get_budget_context() -> dict:
    return {'target_month': '2026年03月', 'is_demo': True, **_demo_budget_overview()}


def get_home_context() -> dict:
    today = date(2026, 3, 27)

    today_tasks = [
        FakeHomeTask(1, '燃えるゴミの日', None, all_day=True, status='completed'),
        FakeHomeTask(2, '歯医者の予約', datetime(2026, 3, 27, 10, 0)),
        FakeHomeTask(3, 'プレゼン資料の作成', datetime(2026, 3, 27, 14, 0), status='in_progress'),
        FakeHomeTask(4, 'ジムでトレーニング', datetime(2026, 3, 27, 19, 0)),
    ]

    habit_status = [
        FakeHabitItem(1, '朝のランニング',      '毎日',  '#28a745', True,  5, 5, True),
        FakeHabitItem(2, '読書30分',            '毎日',  '#28a745', True,  3, 3, True),
        FakeHabitItem(3, '筋トレ',              '週3回', '#28a745', False, 8, 8, True),
        FakeHabitItem(4, 'スマホ使用2時間以内', '毎日',  '#dc3545', False, 4, 4, False),
    ]
    habits_completed = sum(1 for habit in habit_status if habit.completed)

    shopping_items = [
        FakeShoppingItem(1, 'ティッシュペーパー', remaining_count=1, status='insufficient'),
        FakeShoppingItem(2, 'ケーキ（誕生日用）', memo='3月28日 誕生日', remaining_count=0, status='insufficient'),
        FakeShoppingItem(3, 'シャンプー', remaining_count=2, status='available'),
    ]

    type_work = FakeMemoType(1, '仕事', '#6f42c1')
    type_idea = FakeMemoType(2, 'アイデア', '#20c997')
    recent_memos = [
        FakeMemo(1, '4月の目標整理', '', datetime(2026, 3, 26, 21, 30), True, type_idea),
        FakeMemo(2, '会議メモ（新プロジェクト）', '', datetime(2026, 3, 26, 15, 0), False, type_work),
        FakeMemo(3, '読みたい本リスト', '', datetime(2026, 3, 25, 22, 10), False, type_idea),
    ]

    income_total = 285000
    expense_total = 163450

    return {
        'today': today,
        'today_tasks': today_tasks,
        'today_tasks_count': len(today_tasks),
        'habit_status': habit_status,
        'habits_completed': habits_completed,
        'habits_total': len(habit_status),
        'income_total': income_total,
        'expense_total': expense_total,
        'balance_total': income_total - expense_total,
        'target_month': today.strftime('%Y年%m月'),
        'budget_overall': _demo_budget_overview()['overall'],
        'budget_over_count': _demo_budget_overview()['over_count'],
        'shopping_items': shopping_items,
        'shopping_count': len(shopping_items),
        'shopping_insufficient_count': sum(1 for item in shopping_items if item.status == 'insufficient'),
        'recent_memos': recent_memos,
    }
