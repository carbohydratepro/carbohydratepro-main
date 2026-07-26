"""
家計簿サービス：ビジネスロジック
"""
from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from django.db import transaction as db_transaction
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


@db_transaction.atomic
def execute_recurring_payment(
    recurring: RecurringPayment,
    target_date: date,
) -> Transaction | None:
    """定期支払いを同一対象日につき一度だけ実行する。"""
    locked_recurring = (
        RecurringPayment.objects
        .select_for_update()
        .select_related('user', 'category', 'payment_method')
        .get(pk=recurring.pk)
    )
    if not locked_recurring.should_execute_on(target_date):
        return None

    created_transaction = Transaction.objects.create(
        user=locked_recurring.user,
        amount=locked_recurring.amount,
        date=make_aware(datetime.combine(target_date, datetime.min.time())),
        transaction_type=locked_recurring.transaction_type,
        payment_method=locked_recurring.payment_method,
        purpose=locked_recurring.purpose,
        major_category=locked_recurring.major_category,
        category=locked_recurring.category,
        purpose_description=(
            locked_recurring.purpose_description
            or f'定期支払い（{locked_recurring.get_frequency_display()}）'
        ),
    )
    locked_recurring.last_executed = target_date
    locked_recurring.save(update_fields=['last_executed'])
    recurring.last_executed = target_date
    return created_transaction
