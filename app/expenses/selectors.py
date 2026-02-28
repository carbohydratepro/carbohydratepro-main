"""
家計簿セレクター：クエリ・集計・グラフデータ生成ロジック
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from django.db.models import Q, QuerySet, Sum
from django.utils.timezone import make_aware

from project.utils import CHART_COLORS, MAJOR_CATEGORY_LABELS

from .models import Category, PaymentMethod, RecurringPayment, Transaction

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser


def get_date_range(year_month: str | None) -> tuple[datetime, datetime, list[str]]:
    """対象月の開始日・終了日・日付リストを返す。"""
    if year_month:
        target_dt = make_aware(datetime.strptime(year_month, '%Y-%m'))
    else:
        target_dt = make_aware(datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0))

    start_date = target_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_date = (
        (start_date + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        - timedelta(microseconds=1)
    )
    date_range = [
        (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        for i in range((end_date - start_date).days + 1)
    ]
    return start_date, end_date, date_range


def get_transactions(
    user: AbstractBaseUser,
    start_date: datetime,
    end_date: datetime,
    *,
    search: str = '',
    transaction_type: str = '',
    major_category: str = '',
    category_id: str = '',
    payment_method_id: str = '',
) -> QuerySet:
    """フィルタリング済みの取引クエリセットを返す。"""
    qs = (
        Transaction.objects.filter(user=user, date__range=(start_date, end_date))
        .select_related('payment_method', 'category')
        .order_by('-date', '-id')
    )
    if search:
        qs = qs.filter(
            Q(purpose__icontains=search)
            | Q(purpose_description__icontains=search)
            | Q(category__name__icontains=search)
            | Q(payment_method__name__icontains=search)
        )
    if transaction_type:
        qs = qs.filter(transaction_type=transaction_type)
    if major_category:
        qs = qs.filter(major_category=major_category)
    if category_id:
        qs = qs.filter(category__id=category_id)
    if payment_method_id:
        qs = qs.filter(payment_method__id=payment_method_id)
    return qs


def get_summary(transactions_qs: QuerySet) -> dict[str, Decimal | float]:
    """月合計の収入・支出・純残高を返す。"""
    total_income: Decimal = (
        transactions_qs.filter(transaction_type='income').aggregate(Sum('amount'))['amount__sum']
        or Decimal('0')
    )
    total_expense: Decimal = (
        transactions_qs.filter(transaction_type='expense').aggregate(Sum('amount'))['amount__sum']
        or Decimal('0')
    )
    net_balance: float = float(total_income) - float(total_expense)
    return {'total_income': total_income, 'total_expense': total_expense, 'net_balance': net_balance}


def build_category_chart_data(transactions_qs: QuerySet) -> str:
    """カテゴリ別グラフデータ（JSON文字列）を返す。支出のみ、上位5件＋その他。"""
    expense_qs = transactions_qs.filter(transaction_type='expense')
    category_data = expense_qs.values('category__name').annotate(total=Sum('amount')).order_by('-total')

    if category_data.exists():
        top_categories = list(category_data[:5])
        other_total = sum(float(entry['total']) for entry in category_data[5:])
        labels = [
            entry['category__name'][:10] + ('...' if len(entry['category__name']) > 10 else '')
            for entry in top_categories
        ]
        amounts = [float(entry['total']) for entry in top_categories]
        colors: list[str] = CHART_COLORS['category'][: len(labels)]
        if other_total > 0:
            labels.append('その他')
            amounts.append(other_total)
            colors.append(CHART_COLORS['no_data'])
    else:
        labels = ['データなし']
        amounts = [1]
        colors = [CHART_COLORS['no_data']]

    return json.dumps({'labels': labels, 'datasets': [{'data': amounts, 'backgroundColor': colors}]})


def build_major_category_chart_data(transactions_qs: QuerySet) -> str:
    """大分類別グラフデータ（JSON文字列）を返す。支出のみ、固定3色。"""
    expense_qs = transactions_qs.filter(transaction_type='expense')
    major_data = expense_qs.values('major_category').annotate(total=Sum('amount')).order_by('-total')

    if major_data.exists():
        colors = [CHART_COLORS['major_category'][entry['major_category']] for entry in major_data]
        return json.dumps({
            'labels': [MAJOR_CATEGORY_LABELS[entry['major_category']] for entry in major_data],
            'datasets': [{'data': [float(entry['total']) for entry in major_data], 'backgroundColor': colors}],
        })
    return json.dumps({
        'labels': ['データなし'],
        'datasets': [{'data': [1], 'backgroundColor': [CHART_COLORS['no_data']]}],
    })


def build_daily_chart_data(transactions_qs: QuerySet, date_range: list[str]) -> tuple[str, str]:
    """日別支出グラフ・残高グラフのデータ（JSON文字列のタプル）を返す。"""
    expense_data: list[float] = []
    balance_data: list[float] = []
    current_balance: float = 0.0

    for d in date_range:
        daily_expense = float(
            transactions_qs.filter(date__date=d, transaction_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        )
        daily_income = float(
            transactions_qs.filter(date__date=d, transaction_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        )
        current_balance += daily_income - daily_expense
        expense_data.append(daily_expense)
        balance_data.append(current_balance)

    expense_json = json.dumps({
        'labels': date_range,
        'datasets': [{'label': '支出', 'data': expense_data, 'backgroundColor': CHART_COLORS['expense_bar']}],
    })
    balance_json = json.dumps({
        'labels': date_range,
        'datasets': [{'label': '所持金', 'data': balance_data, 'fill': False, 'borderColor': CHART_COLORS['balance_line']}],
    })
    return expense_json, balance_json


def get_payment_methods(user: AbstractBaseUser) -> QuerySet:
    """ユーザーの支払方法一覧を返す。"""
    return PaymentMethod.objects.filter(user=user)


def get_categories(user: AbstractBaseUser) -> QuerySet:
    """ユーザーのカテゴリ一覧を返す。"""
    return Category.objects.filter(user=user)


def get_recurring_payments(user: AbstractBaseUser) -> QuerySet:
    """ユーザーの定期支払い一覧を返す（アクティブ優先・作成日降順）。"""
    return (
        RecurringPayment.objects.filter(user=user)
        .select_related('category', 'payment_method')
        .order_by('-is_active', '-created_at')
    )
