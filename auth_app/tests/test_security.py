"""
セキュリティ関連機能のテスト（ログインロック）
"""
from datetime import timedelta

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from auth_app import services
from auth_app.forms import LOGIN_LOCKED_MESSAGE
from auth_app.models import LoginHistory
from tests.factories import UserFactory


@override_settings(LOGIN_LOCKOUT_THRESHOLD=5, LOGIN_LOCKOUT_WINDOW_MINUTES=15)
class LoginLockoutTest(TestCase):
    """ログイン失敗による一時ロックのテスト"""

    def setUp(self) -> None:
        self.client = Client()
        self.password = 'testpass123'
        self.user = UserFactory()

    def _create_failures(self, count: int, minutes_ago: int = 0) -> None:
        login_time = timezone.now() - timedelta(minutes=minutes_ago)
        for _ in range(count):
            LoginHistory.objects.create(
                user=self.user,
                ip_address='203.0.113.10',
                success=False,
                login_time=login_time,
            )

    def test_not_locked_below_threshold(self) -> None:
        """閾値未満の失敗ではロックされないこと"""
        self._create_failures(4)
        self.assertFalse(services.is_login_locked(self.user.email))

    def test_locked_at_threshold(self) -> None:
        """閾値に達するとロックされること"""
        self._create_failures(5)
        self.assertTrue(services.is_login_locked(self.user.email))

    def test_lock_expires_after_window(self) -> None:
        """ウィンドウ経過後の失敗はカウントされないこと"""
        self._create_failures(5, minutes_ago=20)
        self.assertFalse(services.is_login_locked(self.user.email))

    def test_success_resets_failure_count(self) -> None:
        """成功後の失敗のみカウントされること"""
        self._create_failures(5, minutes_ago=10)
        LoginHistory.objects.create(
            user=self.user,
            ip_address='203.0.113.10',
            success=True,
            login_time=timezone.now() - timedelta(minutes=5),
        )
        self.assertFalse(services.is_login_locked(self.user.email))

    def test_unknown_email_is_not_locked(self) -> None:
        """存在しないメールアドレスはロック対象外であること"""
        self.assertFalse(services.is_login_locked('nonexistent@example.com'))

    def test_login_rejected_while_locked_even_with_correct_password(self) -> None:
        """ロック中は正しいパスワードでもログインできないこと"""
        for _ in range(5):
            self.client.post(
                reverse('login'),
                {'username': self.user.email, 'password': 'wrongpassword'},
            )
        response = self.client.post(
            reverse('login'),
            {'username': self.user.email, 'password': self.password},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, LOGIN_LOCKED_MESSAGE)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_locked_attempt_does_not_extend_lock(self) -> None:
        """ロック中の試行では失敗履歴が増えないこと（ロックが自動解除されるため）"""
        for _ in range(5):
            self.client.post(
                reverse('login'),
                {'username': self.user.email, 'password': 'wrongpassword'},
            )
        failure_count = LoginHistory.objects.filter(user=self.user, success=False).count()
        self.client.post(
            reverse('login'),
            {'username': self.user.email, 'password': self.password},
        )
        self.assertEqual(
            LoginHistory.objects.filter(user=self.user, success=False).count(),
            failure_count,
        )
