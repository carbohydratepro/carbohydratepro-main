"""
家計簿サービス：ビジネスロジック
"""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from django.utils.timezone import make_aware

from .models import Category, PaymentMethod, RecurringPayment, Transaction

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser

PAYMENT_METHOD_LIMIT = 10
CATEGORY_LIMIT = 10


def is_payment_method_limit_reached(user: AbstractBaseUser) -> bool:
    """支払方法の登録上限に達しているか判定する。"""
    return PaymentMethod.objects.filter(user=user).count() >= PAYMENT_METHOD_LIMIT


def is_category_limit_reached(user: AbstractBaseUser) -> bool:
    """カテゴリの登録上限に達しているか判定する。"""
    return Category.objects.filter(user=user).count() >= CATEGORY_LIMIT


def execute_recurring_payment(recurring: RecurringPayment, target_date: date) -> Transaction:
    """定期支払いを実行し、Transaction を作成して返す。last_executed を更新する。"""
    transaction = Transaction.objects.create(
        user=recurring.user,
        amount=recurring.amount,
        date=make_aware(datetime.combine(target_date, datetime.min.time())),
        transaction_type=recurring.transaction_type,
        payment_method=recurring.payment_method,
        purpose=recurring.purpose,
        major_category=recurring.major_category,
        category=recurring.category,
        purpose_description=recurring.purpose_description or f'定期支払い（{recurring.get_frequency_display()}）',
    )
    recurring.last_executed = target_date
    recurring.save(update_fields=['last_executed'])
    return transaction
