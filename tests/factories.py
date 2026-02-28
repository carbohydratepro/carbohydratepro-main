"""
テスト用ファクトリクラス。

使い方:
    from tests.factories import UserFactory, TransactionFactory

    # デフォルト値でオブジェクトを作成
    user = UserFactory()
    transaction = TransactionFactory()

    # 特定の値を指定して作成
    user = UserFactory(email='custom@example.com')
    transaction = TransactionFactory(user=user, amount=Decimal('500.00'))

    # 複数まとめて作成
    users = UserFactory.create_batch(5)
"""

import datetime
from decimal import Decimal

import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from app.expenses.models import Category, PaymentMethod, RecurringPayment, Transaction
from app.memo.models import Memo, MemoType
from app.models import ContactMessage
from app.shopping.models import ShoppingItem
from app.task.models import Task, TaskLabel
from auth_app.models import EmailVerificationToken, LoginHistory


class UserFactory(DjangoModelFactory):
    """CustomUser ファクトリ。デフォルトでメール認証済み・パスワード 'testpass123'。"""

    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    is_active = True
    is_email_verified = True
    # set_password を呼び出してパスワードをハッシュ化し、その後 save() を実行
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')


class LoginHistoryFactory(DjangoModelFactory):
    """LoginHistory ファクトリ。"""

    class Meta:
        model = LoginHistory

    user = factory.SubFactory(UserFactory)
    ip_address = '127.0.0.1'
    user_agent = 'TestAgent/1.0'
    success = True


class EmailVerificationTokenFactory(DjangoModelFactory):
    """EmailVerificationToken ファクトリ。expires_at は save() で自動設定される。"""

    class Meta:
        model = EmailVerificationToken

    user = factory.SubFactory(UserFactory)


class PaymentMethodFactory(DjangoModelFactory):
    """PaymentMethod ファクトリ。"""

    class Meta:
        model = PaymentMethod

    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f'支払方法{n}')


class CategoryFactory(DjangoModelFactory):
    """Category ファクトリ。"""

    class Meta:
        model = Category

    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f'カテゴリ{n}')


class TransactionFactory(DjangoModelFactory):
    """Transaction ファクトリ。payment_method と category は user と同じユーザーに紐づく。"""

    class Meta:
        model = Transaction

    user = factory.SubFactory(UserFactory)
    amount = Decimal('1000.00')
    date = factory.LazyFunction(lambda: datetime.datetime.now(tz=datetime.timezone.utc))
    transaction_type = 'expense'
    major_category = 'variable'
    purpose = factory.Sequence(lambda n: f'支出{n}')
    purpose_description = ''
    payment_method = factory.SubFactory(
        PaymentMethodFactory,
        user=factory.SelfAttribute('..user'),
    )
    category = factory.SubFactory(
        CategoryFactory,
        user=factory.SelfAttribute('..user'),
    )


class RecurringPaymentFactory(DjangoModelFactory):
    """RecurringPayment ファクトリ。デフォルトは月次・1日実行。"""

    class Meta:
        model = RecurringPayment

    user = factory.SubFactory(UserFactory)
    purpose = factory.Sequence(lambda n: f'定期支払{n}')
    amount = Decimal('1000.00')
    frequency = 'monthly'
    days_of_month = [1]
    category = factory.SubFactory(
        CategoryFactory,
        user=factory.SelfAttribute('..user'),
    )
    payment_method = factory.SubFactory(
        PaymentMethodFactory,
        user=factory.SelfAttribute('..user'),
    )


class TaskLabelFactory(DjangoModelFactory):
    """TaskLabel ファクトリ。"""

    class Meta:
        model = TaskLabel

    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f'ラベル{n}')
    color = '#6c757d'


class TaskFactory(DjangoModelFactory):
    """Task ファクトリ。デフォルトは未着手・優先度中。"""

    class Meta:
        model = Task

    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f'タスク{n}')
    priority = 'medium'
    status = 'not_started'


class MemoTypeFactory(DjangoModelFactory):
    """MemoType ファクトリ。"""

    class Meta:
        model = MemoType

    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f'メモ種別{n}')
    color = '#6c757d'


class MemoFactory(DjangoModelFactory):
    """Memo ファクトリ。memo_type は user と同じユーザーに紐づく。"""

    class Meta:
        model = Memo

    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f'メモ{n}')
    memo_type = factory.SubFactory(
        MemoTypeFactory,
        user=factory.SelfAttribute('..user'),
    )
    content = ''


class ShoppingItemFactory(DjangoModelFactory):
    """ShoppingItem ファクトリ。デフォルトは一回限り・在庫不足状態。"""

    class Meta:
        model = ShoppingItem

    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f'商品{n}')
    frequency = 'one_time'
    remaining_count = 0
    threshold_count = 0


class ContactMessageFactory(DjangoModelFactory):
    """ContactMessage ファクトリ。"""

    class Meta:
        model = ContactMessage

    user = factory.SubFactory(UserFactory)
    inquiry_type = 'question'
    subject = factory.Sequence(lambda n: f'件名{n}')
    message = 'テストメッセージ'
