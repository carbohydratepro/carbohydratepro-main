"""
リスト表示・ページネーション・フィルタリングの統合テスト
"""
from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from app.expenses.models import Transaction, PaymentMethod, Category
from app.memo.models import Memo, MemoType
from app.shopping.models import ShoppingItem
from app.task.models import Task, TaskLabel


@override_settings(
    SITE_DOMAIN='example.com',
    SITE_PROTOCOL='http',
    SITE_NAME='CarbohydratePro',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class ExpensesListViewTest(TestCase):
    """支出一覧のページネーション・フィルタリングテスト"""

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email='user@example.com',
            username='tester',
            password='pass12345',
            is_email_verified=True
        )
        self.client.login(username=self.user.email, password='pass12345')

    def _create_expense_data(self, count: int = 25) -> tuple:
        """テスト用の支出データを作成（同じ月内にすべてのデータを作成）"""
        pay = PaymentMethod.objects.create(user=self.user, name='カード')
        cat = Category.objects.create(user=self.user, name='食費')
        # 月の15日を基準にして、前後にデータを作成（月をまたがないように）
        base_date = timezone.now().replace(day=15, hour=12, minute=0, second=0, microsecond=0)
        for i in range(count):
            # -12日から+12日の範囲でデータを作成（月をまたがない）
            offset = i - count // 2
            Transaction.objects.create(
                user=self.user,
                amount=1000 + i,
                date=base_date + timedelta(hours=i),  # 同じ日の異なる時間に作成
                transaction_type='expense',
                payment_method=pay,
                purpose=f'用途{i}',
                major_category='variable',
                category=cat,
                purpose_description='',
            )
        return pay, cat

    def test_default_pagination_20(self) -> None:
        """デフォルトのページネーション（20件）のテスト"""
        self._create_expense_data(25)
        resp = self.client.get(reverse('expense_list'))
        page = resp.context['transactions_page']
        self.assertEqual(page.paginator.per_page, 20)
        self.assertEqual(page.paginator.count, 25)
        self.assertEqual(len(page.object_list), 20)

    def test_per_page_10(self) -> None:
        """ページあたり10件のテスト"""
        self._create_expense_data(12)
        resp = self.client.get(reverse('expense_list') + '?per_page=10')
        page = resp.context['transactions_page']
        self.assertEqual(page.paginator.per_page, 10)
        self.assertEqual(page.paginator.count, 12)
        self.assertEqual(len(page.object_list), 10)

    def test_filter_by_transaction_type(self) -> None:
        """取引タイプでのフィルタリングテスト"""
        pay = PaymentMethod.objects.create(user=self.user, name='カード')
        cat = Category.objects.create(user=self.user, name='食費')
        Transaction.objects.create(
            user=self.user,
            amount=1000,
            date=timezone.now(),
            transaction_type='income',
            payment_method=pay,
            purpose='給料',
            major_category='variable',
            category=cat,
            purpose_description='',
        )
        Transaction.objects.create(
            user=self.user,
            amount=500,
            date=timezone.now(),
            transaction_type='expense',
            payment_method=pay,
            purpose='ランチ',
            major_category='variable',
            category=cat,
            purpose_description='',
        )
        resp = self.client.get(reverse('expense_list') + '?transaction_type=income')
        page = resp.context['transactions_page']
        self.assertEqual(page.paginator.count, 1)
        self.assertEqual(page.object_list[0].transaction_type, 'income')


@override_settings(
    SITE_DOMAIN='example.com',
    SITE_PROTOCOL='http',
    SITE_NAME='CarbohydratePro',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class MemoListViewTest(TestCase):
    """メモ一覧のページネーション・フィルタリングテスト"""

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email='user@example.com',
            username='tester',
            password='pass12345',
            is_email_verified=True
        )
        self.client.login(username=self.user.email, password='pass12345')

    def _ensure_memo_type(self) -> MemoType:
        """共通メモ種別を取得または作成"""
        memo_type, _ = MemoType.objects.get_or_create(
            user=None,
            name='メモ',
            defaults={'color': '#007bff'}
        )
        return memo_type

    def test_pagination(self) -> None:
        """ページネーションのテスト"""
        memo_type = self._ensure_memo_type()
        Memo.objects.bulk_create([
            Memo(user=self.user, title=f'メモ{i}', memo_type=memo_type, content='内容')
            for i in range(25)
        ])
        resp = self.client.get(reverse('memo_list'))
        page = resp.context['page_obj']
        self.assertEqual(page.paginator.per_page, 20)
        self.assertEqual(page.paginator.count, 25)
        self.assertEqual(len(page.object_list), 20)

    def test_per_page_50(self) -> None:
        """ページあたり50件のテスト"""
        memo_type = self._ensure_memo_type()
        Memo.objects.bulk_create([
            Memo(user=self.user, title=f'メモ{i}', memo_type=memo_type, content='内容')
            for i in range(60)
        ])
        resp = self.client.get(reverse('memo_list') + '?per_page=50')
        page = resp.context['page_obj']
        self.assertEqual(page.paginator.per_page, 50)
        self.assertEqual(len(page.object_list), 50)

    def test_filter_by_type_and_favorite(self) -> None:
        """種別とお気に入りでのフィルタリングテスト"""
        memo_type = self._ensure_memo_type()
        idea_type, _ = MemoType.objects.get_or_create(
            user=None,
            name='アイデア',
            defaults={'color': '#28a745'}
        )
        Memo.objects.create(
            user=self.user,
            title='メモ1',
            memo_type=memo_type,
            content='A',
            is_favorite=True
        )
        Memo.objects.create(
            user=self.user,
            title='アイデア1',
            memo_type=idea_type,
            content='B',
            is_favorite=False
        )
        # 種別でフィルタリング
        resp = self.client.get(reverse('memo_list') + f'?memo_type={idea_type.id}')
        page = resp.context['page_obj']
        self.assertEqual(page.paginator.count, 1)
        self.assertEqual(page.object_list[0].memo_type, idea_type)

        # お気に入りでフィルタリング
        resp_fav = self.client.get(reverse('memo_list') + '?favorite=true')
        self.assertEqual(resp_fav.context['page_obj'].paginator.count, 1)
        self.assertTrue(resp_fav.context['page_obj'].object_list[0].is_favorite)


@override_settings(
    SITE_DOMAIN='example.com',
    SITE_PROTOCOL='http',
    SITE_NAME='CarbohydratePro',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class ShoppingListViewTest(TestCase):
    """買い物リスト一覧のテスト"""

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email='user@example.com',
            username='tester',
            password='pass12345',
            is_email_verified=True
        )
        self.client.login(username=self.user.email, password='pass12345')

    def test_groups_items_by_frequency(self) -> None:
        """頻度別グループ分けのテスト"""
        ShoppingItem.objects.create(
            user=self.user,
            title='牛乳',
            frequency='one_time',
            remaining_count=0,
            threshold_count=1
        )
        ShoppingItem.objects.create(
            user=self.user,
            title='米',
            frequency='recurring',
            remaining_count=5,
            threshold_count=2
        )
        resp = self.client.get(reverse('shopping_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['one_time_items']), 1)
        self.assertEqual(len(resp.context['recurring_items']), 1)

    def test_update_counts(self) -> None:
        """残数更新のテスト"""
        item = ShoppingItem.objects.create(
            user=self.user,
            title='水',
            frequency='one_time',
            remaining_count=1,
            threshold_count=0
        )
        resp = self.client.post(
            reverse('update_shopping_count', kwargs={'item_id': item.id}),
            {'field_type': 'remaining', 'action': 'increase'},
        )
        self.assertEqual(resp.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.remaining_count, 2)


@override_settings(
    SITE_DOMAIN='example.com',
    SITE_PROTOCOL='http',
    SITE_NAME='CarbohydratePro',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class TaskListViewTest(TestCase):
    """タスク一覧のページネーション・フィルタリングテスト"""

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email='user@example.com',
            username='tester',
            password='pass12345',
            is_email_verified=True
        )
        self.client.login(username=self.user.email, password='pass12345')

    def _create_tasks(self, count: int = 25) -> TaskLabel:
        """テスト用のタスクデータを作成"""
        label = TaskLabel.objects.create(user=self.user, name='仕事', color='#000000')
        base_date = timezone.now()
        tasks = []
        for i in range(count):
            tasks.append(
                Task(
                    user=self.user,
                    title=f'タスク{i}',
                    priority='medium',
                    status='not_started',
                    label=label,
                    start_date=base_date + timedelta(days=i),
                    end_date=base_date + timedelta(days=i, hours=1),
                )
            )
        Task.objects.bulk_create(tasks)
        return label

    def test_month_pagination_default(self) -> None:
        """月表示でのデフォルトページネーションのテスト"""
        self._create_tasks(25)
        resp = self.client.get(reverse('task_list'))
        page = resp.context['tasks_page']
        self.assertEqual(page.paginator.per_page, 20)
        self.assertEqual(page.paginator.count, 25)
        self.assertEqual(len(page.object_list), 20)

    def test_day_pagination_10(self) -> None:
        """日表示でのページネーション（10件）のテスト"""
        self._create_tasks(12)
        today_str = timezone.now().date().strftime('%Y-%m-%d')
        resp = self.client.get(
            reverse('task_list') + f'?view_mode=day&target_date={today_str}&per_page=10'
        )
        page = resp.context['tasks_page']
        self.assertEqual(page.paginator.per_page, 10)

    def test_week_start_session_default(self) -> None:
        """週開始日のデフォルト値（日曜日）のテスト"""
        self._create_tasks(3)
        resp = self.client.get(reverse('task_list'))
        self.assertEqual(resp.context['week_start'], 'sunday')
