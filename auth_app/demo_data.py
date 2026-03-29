"""
デモ画面用のフェイクデータを生成するモジュール。
実際のモデルインスタンスに似た属性・メソッドを持つ軽量クラスを使用する。
"""
from __future__ import annotations

import calendar as cal_module
import json
from datetime import date, datetime, timedelta
from django.core.paginator import Paginator


# ---------------------------------------------------------------------------
# 汎用フェイクオブジェクトクラス
# ---------------------------------------------------------------------------

class FakeTransaction:
    _MAJOR_CAT = {'variable': '変動費', 'fixed': '固定費', 'special': '特別費'}
    _TRANS_TYPE = {'income': '収入', 'expense': '支出', 'no_change': '変動なし'}

    def __init__(self, id: int, purpose: str, date_val: date, amount: int,
                 transaction_type: str, payment_method: str, category: str,
                 major_category: str, purpose_description: str | None = None) -> None:
        self.id = id
        self.purpose = purpose
        self.date = date_val
        self.amount = amount
        self.transaction_type = transaction_type
        self.payment_method = payment_method
        self.category = category
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

def get_expenses_context() -> dict:
    transactions = [
        FakeTransaction(1,  '給与',              date(2026, 3, 25), 280000, 'income',   '銀行振込',  '収入',   'variable'),
        FakeTransaction(2,  'スーパー（食材）',  date(2026, 3, 27),   3240, 'expense',  '現金',      '食費',   'variable'),
        FakeTransaction(3,  '電気代',            date(2026, 3, 27),   8200, 'expense',  '口座振替',  '光熱費', 'fixed'),
        FakeTransaction(4,  '家賃',              date(2026, 3,  1),  85000, 'expense',  '口座振替',  '住居費', 'fixed'),
        FakeTransaction(5,  'ランチ',            date(2026, 3, 24),   1050, 'expense',  'カード',    '外食',   'variable'),
        FakeTransaction(6,  '書籍',              date(2026, 3, 22),   2860, 'expense',  'カード',    '教育',   'variable'),
        FakeTransaction(7,  'ジム月会費',        date(2026, 3, 20),   7700, 'expense',  'カード',    '健康',   'fixed'),
        FakeTransaction(8,  '映画',              date(2026, 3, 18),   1800, 'expense',  'カード',    '娯楽',   'variable'),
        FakeTransaction(9,  '水道代',            date(2026, 3, 15),   3500, 'expense',  '口座振替',  '光熱費', 'fixed'),
        FakeTransaction(10, 'コンビニ',          date(2026, 3, 14),    860, 'expense',  '現金',      '日用品', 'variable'),
        FakeTransaction(11, 'スーパー（日用品）',date(2026, 3, 12),   4320, 'expense',  '現金',      '日用品', 'variable'),
        FakeTransaction(12, '交通費（定期）',    date(2026, 3, 10),   9800, 'expense',  'カード',    '交通',   'fixed'),
        FakeTransaction(13, 'カフェ',            date(2026, 3,  9),    680, 'expense',  'カード',    '外食',   'variable'),
        FakeTransaction(14, 'プレゼント代',      date(2026, 3,  5),  16000, 'expense',  'カード',    'ギフト', 'special'),
        FakeTransaction(15, '保険料',            date(2026, 3,  1),   9710, 'expense',  '口座振替',  '保険',   'fixed'),
    ]

    paginator = Paginator(transactions, 20)
    transactions_page = paginator.get_page(1)

    categories = [
        FakeCategory(1, '食費'),   FakeCategory(2, '外食'),   FakeCategory(3, '光熱費'),
        FakeCategory(4, '住居費'), FakeCategory(5, '教育'),   FakeCategory(6, '健康'),
        FakeCategory(7, '娯楽'),   FakeCategory(8, '日用品'), FakeCategory(9, '交通'),
        FakeCategory(10, 'ギフト'), FakeCategory(11, '保険'), FakeCategory(12, '収入'),
    ]
    payment_methods = [
        FakePaymentMethod(1, '現金'), FakePaymentMethod(2, 'カード'),
        FakePaymentMethod(3, '銀行振込'), FakePaymentMethod(4, '口座振替'),
    ]

    total_income = 280000
    total_expense = 154720
    net_balance = total_income - total_expense

    category_data_json = json.dumps({
        'labels': ['住居費', '保険', '交通', '健康', '光熱費', '日用品', '食費', 'ギフト', '教育', '外食', '娯楽'],
        'datasets': [{'data': [85000, 9710, 9800, 7700, 11700, 5180, 8400, 16000, 2860, 1730, 1800],
                      'backgroundColor': ['#4e79a7','#f28e2b','#e15759','#76b7b2','#59a14f','#edc948','#b07aa1','#ff9da7','#9c755f','#bab0ac','#86bcb6']}],
    })
    major_category_data_json = json.dumps({
        'labels': ['変動費', '固定費', '特別費'],
        'datasets': [{'data': [29470, 109210, 16000],
                      'backgroundColor': ['#4e79a7', '#f28e2b', '#e15759']}],
    })
    _expense_vals = [94710,0,0,0,16000,0,0,0,680,9800,0,4320,0,860,3500,0,0,1800,0,7700,0,2860,0,1050,0,0,11440,0,0,0]
    _balance_vals = [-94710,-94710,-94710,-94710,-110710,-110710,-110710,-110710,
                     -111390,-121190,-121190,-125510,-125510,-126370,-129870,-129870,
                     -129870,-131670,-131670,-139370,-139370,-142230,-142230,-143280,
                     136720,136720,125280,125280,125280,125280]
    _day_labels   = [f'2026-03-{str(i).zfill(2)}' for i in range(1, 32)]
    expense_data_json = json.dumps({
        'labels': _day_labels,
        'datasets': [{'label': '支出', 'data': _expense_vals, 'backgroundColor': 'rgba(255,99,132,0.5)'}],
    })
    balance_data_json = json.dumps({
        'labels': _day_labels,
        'datasets': [{'label': '所持金', 'data': _balance_vals, 'fill': False, 'borderColor': 'rgba(54,162,235,0.8)'}],
    })

    return {
        'view_mode':              'month',
        'transactions_page':      transactions_page,
        'transactions_count':     len(transactions),
        'category_data_json':     category_data_json,
        'major_category_data_json': major_category_data_json,
        'expense_data_json':      expense_data_json,
        'balance_data_json':      balance_data_json,
        'total_income':           total_income,
        'total_expense':          total_expense,
        'net_balance':            net_balance,
        'total_income_formatted': f'{total_income:,.0f}',
        'total_expense_formatted':f'{total_expense:,.0f}',
        'net_balance_formatted':  f'{net_balance:,.0f}',
        'target_month':           '2026年3月',
        'search_query':           '',
        'user_categories':        categories,
        'user_payment_methods':   payment_methods,
        'filter_transaction_type':'',
        'filter_major_category':  '',
        'filter_category':        '',
        'filter_payment_method':  '',
        'default_target_date':    '2026-03',
        'per_page':               20,
        'per_page_options':       ['10', '20', '50', '100'],
        'sort_by':                'date_desc',
        'year_for_toggle':        2026,
        'month_for_toggle':       '2026-03',
    }


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

    return {
        'selected_date':  today.isoformat(),
        'min_date':       '2025-01-01',
        'today':          today.isoformat(),
        'today_status':   today_status,
        'week_header_data': week_header_data,
        'week_data':      week_data,
        'selected_year':  None,
        'year_choices':   [2025, 2026],
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


def get_task_settings_context() -> dict:
    labels = [
        FakeLabel('#e83e8c', 1, '仕事'),
        FakeLabel('#20c997', 2, '健康'),
        FakeLabel('#fd7e14', 3, '勉強'),
        FakeLabel('#6f42c1', 4, 'プライベート'),
    ]
    return {
        'labels': labels,
        'current_week_start': 'sunday',
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
