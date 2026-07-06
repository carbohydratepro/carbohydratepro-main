"""
統合ダッシュボード（ホーム画面）のテスト
"""
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.habit.models import Habit, HabitRecord
from tests.factories import (
    MemoFactory,
    ShoppingItemFactory,
    TaskFactory,
    TransactionFactory,
    UserFactory,
)


def aware_today_at(hour: int) -> datetime:
    """今日（ローカル日付）の指定時刻のawareなdatetimeを返す。"""
    return timezone.make_aware(datetime.combine(timezone.localdate(), time(hour, 0)))


@override_settings(
    SITE_DOMAIN='example.com',
    SITE_PROTOCOL='http',
    SITE_NAME='CarbohydratePro',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class DashboardViewTest(TestCase):
    """ダッシュボード表示のテスト"""

    def setUp(self) -> None:
        self.client = Client()
        self.user = UserFactory()
        self.client.login(username=self.user.email, password='testpass123')

    def test_login_required(self) -> None:
        """未認証はログイン画面へリダイレクトされること"""
        self.client.logout()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_dashboard_renders_sections(self) -> None:
        """主要セクションが表示されること"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ホーム')
        self.assertContains(response, '今月の収支')
        self.assertContains(response, '今日のタスク')
        self.assertContains(response, '今日の習慣')
        self.assertContains(response, '買い物リスト')
        self.assertContains(response, '最近のメモ')

    def test_monthly_summary_totals(self) -> None:
        """今月の収支が正しく集計されること（先月分は除外）"""
        now = timezone.now()
        TransactionFactory(user=self.user, transaction_type='income', amount=Decimal('5000'), date=now)
        TransactionFactory(user=self.user, transaction_type='expense', amount=Decimal('1200'), date=now)
        TransactionFactory(user=self.user, transaction_type='expense', amount=Decimal('9999'), date=now - timedelta(days=40))

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['income_total'], Decimal('5000'))
        self.assertEqual(response.context['expense_total'], Decimal('1200'))
        self.assertEqual(response.context['balance_total'], Decimal('3800'))

    def test_today_tasks_filtering(self) -> None:
        """今日のタスクのみ表示されること（明日・他ユーザーは除外）"""
        TaskFactory(user=self.user, title='今日の予定', start_date=aware_today_at(10), end_date=aware_today_at(11))
        TaskFactory(user=self.user, title='明日の予定', start_date=aware_today_at(10) + timedelta(days=1), end_date=aware_today_at(11) + timedelta(days=1))
        other_user = UserFactory()
        TaskFactory(user=other_user, title='他人の予定', start_date=aware_today_at(10), end_date=aware_today_at(11))

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, '今日の予定')
        self.assertNotContains(response, '明日の予定')
        self.assertNotContains(response, '他人の予定')
        self.assertEqual(response.context['today_tasks_count'], 1)

    def test_habit_completion_status(self) -> None:
        """今日の習慣の達成状況が表示されること"""
        done = Habit.objects.create(user=self.user, title='達成済みの習慣')
        Habit.objects.create(user=self.user, title='未達成の習慣')
        HabitRecord.objects.create(habit=done, date=timezone.localdate())

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, '達成済みの習慣')
        self.assertContains(response, '未達成の習慣')
        self.assertEqual(response.context['habits_completed'], 1)
        self.assertEqual(response.context['habits_total'], 2)

    def test_shopping_unchecked_only(self) -> None:
        """未購入の商品のみ表示されること"""
        ShoppingItemFactory(user=self.user, title='未購入の品')
        ShoppingItemFactory(user=self.user, title='購入済みの品', is_checked=True)

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, '未購入の品')
        self.assertNotContains(response, '購入済みの品')
        self.assertEqual(response.context['shopping_count'], 1)

    def test_recent_memos_shown(self) -> None:
        """最近のメモが表示されること"""
        MemoFactory(user=self.user, title='直近のメモ')
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, '直近のメモ')


class DemoHomeViewTest(TestCase):
    """デモ用ホーム画面のテスト"""

    def test_demo_home_renders(self) -> None:
        """ログイン不要でデモホームが表示されること"""
        response = Client().get(reverse('demo_home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '今月の収支')
        self.assertContains(response, 'デモモード')
