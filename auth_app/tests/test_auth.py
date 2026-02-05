"""
認証機能のテスト
"""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone

from auth_app.models import EmailVerificationToken, LoginHistory


@override_settings(
    SITE_DOMAIN='example.com',
    SITE_PROTOCOL='http',
    SITE_NAME='CarbohydratePro',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class CustomUserModelTest(TestCase):
    """カスタムユーザーモデルのテスト"""

    def test_create_user(self) -> None:
        """通常ユーザーの作成テスト"""
        User = get_user_model()
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_email_verified)

    def test_create_user_without_email_raises(self) -> None:
        """メールアドレスなしでユーザー作成するとエラーが発生することをテスト"""
        User = get_user_model()
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', username='testuser', password='test123')

    def test_create_superuser(self) -> None:
        """スーパーユーザーの作成テスト"""
        User = get_user_model()
        admin = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='adminpass123'
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)

    def test_user_str(self) -> None:
        """ユーザーの文字列表現テスト"""
        User = get_user_model()
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.assertEqual(str(user), 'test@example.com')


@override_settings(
    SITE_DOMAIN='example.com',
    SITE_PROTOCOL='http',
    SITE_NAME='CarbohydratePro',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class EmailVerificationTokenTest(TestCase):
    """メール認証トークンモデルのテスト"""

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_create_token(self) -> None:
        """トークンの作成テスト"""
        token = EmailVerificationToken.objects.create(user=self.user)
        self.assertIsNotNone(token.token)
        self.assertFalse(token.is_verified)
        self.assertIsNotNone(token.expires_at)

    def test_token_is_valid(self) -> None:
        """有効なトークンのテスト"""
        token = EmailVerificationToken.objects.create(user=self.user)
        self.assertTrue(token.is_valid())

    def test_token_expired(self) -> None:
        """期限切れトークンのテスト"""
        token = EmailVerificationToken.objects.create(user=self.user)
        token.expires_at = timezone.now() - timedelta(hours=1)
        token.save()
        self.assertFalse(token.is_valid())

    def test_token_already_verified(self) -> None:
        """認証済みトークンのテスト"""
        token = EmailVerificationToken.objects.create(user=self.user)
        token.is_verified = True
        token.save()
        self.assertFalse(token.is_valid())


@override_settings(
    SITE_DOMAIN='example.com',
    SITE_PROTOCOL='http',
    SITE_NAME='CarbohydratePro',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class LoginHistoryModelTest(TestCase):
    """ログイン履歴モデルのテスト"""

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_create_login_history(self) -> None:
        """ログイン履歴の作成テスト"""
        history = LoginHistory.objects.create(
            user=self.user,
            ip_address='127.0.0.1',
            user_agent='Test Browser',
            success=True
        )
        self.assertEqual(history.user, self.user)
        self.assertTrue(history.success)
        self.assertIn('成功', str(history))

    def test_failed_login_history(self) -> None:
        """失敗ログイン履歴のテスト"""
        history = LoginHistory.objects.create(
            user=self.user,
            ip_address='127.0.0.1',
            success=False
        )
        self.assertFalse(history.success)
        self.assertIn('失敗', str(history))


@override_settings(
    SITE_DOMAIN='example.com',
    SITE_PROTOCOL='http',
    SITE_NAME='CarbohydratePro',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class LoginViewTest(TestCase):
    """ログインビューのテスト"""

    def setUp(self) -> None:
        self.client = Client()
        User = get_user_model()
        self.password = 'testpass123'
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password=self.password,
            is_email_verified=True,
        )

    def test_login_page_loads(self) -> None:
        """ログインページの表示テスト"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_success(self) -> None:
        """ログイン成功テスト"""
        response = self.client.post(
            reverse('login'),
            {'username': self.user.email, 'password': self.password}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_invalid_credentials(self) -> None:
        """ログイン失敗テスト（誤った資格情報）"""
        response = self.client.post(
            reverse('login'),
            {'username': self.user.email, 'password': 'wrongpassword'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'メールアドレスとパスワードが一致しません。')

    def test_login_nonexistent_user(self) -> None:
        """存在しないユーザーでのログインテスト"""
        response = self.client.post(
            reverse('login'),
            {'username': 'nonexistent@example.com', 'password': 'anypassword'}
        )
        self.assertEqual(response.status_code, 200)


@override_settings(
    SITE_DOMAIN='example.com',
    SITE_PROTOCOL='http',
    SITE_NAME='CarbohydratePro',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class SignupViewTest(TestCase):
    """サインアップビューのテスト"""

    def setUp(self) -> None:
        self.client = Client()
        User = get_user_model()
        self.existing_user = User.objects.create_user(
            email='existing@example.com',
            username='existinguser',
            password='testpass123',
        )

    def test_signup_page_loads(self) -> None:
        """サインアップページの表示テスト"""
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)

    @patch('auth_app.views.send_html_email', return_value=True)
    def test_signup_success(self, mock_send_email) -> None:
        """サインアップ成功テスト"""
        User = get_user_model()
        signup_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'newpassword123',
            'password2': 'newpassword123',
        }
        response = self.client.post(reverse('signup'), signup_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='new@example.com').exists())
        mock_send_email.assert_called_once()

    def test_signup_duplicate_username(self) -> None:
        """ユーザー名重複時のテスト"""
        signup_data = {
            'username': self.existing_user.username,
            'email': 'other@example.com',
            'password1': 'somepassword123',
            'password2': 'somepassword123',
        }
        response = self.client.post(reverse('signup'), signup_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'このユーザー名は使われています。')

    def test_signup_duplicate_email(self) -> None:
        """メールアドレス重複時のテスト"""
        signup_data = {
            'username': 'anotheruser',
            'email': self.existing_user.email,
            'password1': 'somepassword123',
            'password2': 'somepassword123',
        }
        response = self.client.post(reverse('signup'), signup_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'このメールアドレスは使われています。')

    def test_signup_password_mismatch(self) -> None:
        """パスワード不一致時のテスト"""
        signup_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'password123',
            'password2': 'differentpassword',
        }
        response = self.client.post(reverse('signup'), signup_data)
        self.assertEqual(response.status_code, 200)


@override_settings(
    SITE_DOMAIN='example.com',
    SITE_PROTOCOL='http',
    SITE_NAME='CarbohydratePro',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class EmailVerificationViewTest(TestCase):
    """メール認証ビューのテスト"""

    def setUp(self) -> None:
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=False,
        )
        self.token = EmailVerificationToken.objects.create(user=self.user)

    def test_verify_email_success(self) -> None:
        """メール認証成功テスト"""
        response = self.client.get(
            reverse('verify_email', kwargs={'token': self.token.token})
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
        self.token.refresh_from_db()
        self.assertTrue(self.token.is_verified)

    def test_verify_email_invalid_token(self) -> None:
        """無効なトークンでの認証テスト"""
        import uuid
        invalid_token = uuid.uuid4()
        response = self.client.get(
            reverse('verify_email', kwargs={'token': invalid_token})
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)

    def test_verify_email_expired_token(self) -> None:
        """期限切れトークンでの認証テスト"""
        self.token.expires_at = timezone.now() - timedelta(hours=1)
        self.token.save()
        response = self.client.get(
            reverse('verify_email', kwargs={'token': self.token.token})
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)


@override_settings(
    SITE_DOMAIN='example.com',
    SITE_PROTOCOL='http',
    SITE_NAME='CarbohydratePro',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class ResendVerificationViewTest(TestCase):
    """メール認証再送信ビューのテスト"""

    def setUp(self) -> None:
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=False,
        )

    def test_resend_verification_page_loads(self) -> None:
        """再送信ページの表示テスト"""
        response = self.client.get(reverse('resend_verification'))
        self.assertEqual(response.status_code, 200)

    @patch('auth_app.views.send_html_email', return_value=True)
    def test_resend_verification_success(self, mock_send_email) -> None:
        """再送信成功テスト"""
        response = self.client.post(
            reverse('resend_verification'),
            {'email': self.user.email}
        )
        self.assertEqual(response.status_code, 302)
        mock_send_email.assert_called_once()

    def test_resend_verification_already_verified(self) -> None:
        """認証済みユーザーへの再送信テスト"""
        self.user.is_email_verified = True
        self.user.save()
        response = self.client.post(
            reverse('resend_verification'),
            {'email': self.user.email}
        )
        self.assertEqual(response.status_code, 302)


@override_settings(
    SITE_DOMAIN='example.com',
    SITE_PROTOCOL='http',
    SITE_NAME='CarbohydratePro',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class PasswordResetViewTest(TestCase):
    """パスワードリセットビューのテスト"""

    def setUp(self) -> None:
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )

    def test_password_reset_page_loads(self) -> None:
        """パスワードリセットページの表示テスト"""
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)

    @patch('auth_app.views.send_html_email', return_value=True)
    def test_password_reset_request_success(self, mock_send_email) -> None:
        """パスワードリセット申請成功テスト"""
        response = self.client.post(
            reverse('password_reset'),
            {'email': self.user.email}
        )
        self.assertEqual(response.status_code, 302)
        mock_send_email.assert_called_once()

    def test_password_reset_nonexistent_email(self) -> None:
        """存在しないメールアドレスでの申請テスト"""
        response = self.client.post(
            reverse('password_reset'),
            {'email': 'nonexistent@example.com'}
        )
        self.assertEqual(response.status_code, 302)


@override_settings(
    SITE_DOMAIN='example.com',
    SITE_PROTOCOL='http',
    SITE_NAME='CarbohydratePro',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class MyPageViewTest(TestCase):
    """マイページビューのテスト"""

    def setUp(self) -> None:
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )
        self.client.login(username='test@example.com', password='testpass123')

    def test_my_page_requires_login(self) -> None:
        """マイページに認証が必要であることをテスト"""
        self.client.logout()
        response = self.client.get(reverse('my_page', kwargs={'pk': self.user.pk}))
        self.assertNotEqual(response.status_code, 200)

    def test_my_page_view(self) -> None:
        """マイページ表示テスト"""
        response = self.client.get(reverse('my_page', kwargs={'pk': self.user.pk}))
        self.assertEqual(response.status_code, 200)

    def test_my_page_other_user_forbidden(self) -> None:
        """他ユーザーのマイページアクセスが禁止されることをテスト"""
        User = get_user_model()
        other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            password='testpass123',
            is_email_verified=True,
        )
        response = self.client.get(reverse('my_page', kwargs={'pk': other_user.pk}))
        self.assertEqual(response.status_code, 403)


@override_settings(
    SITE_DOMAIN='example.com',
    SITE_PROTOCOL='http',
    SITE_NAME='CarbohydratePro',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class PasswordChangeViewTest(TestCase):
    """パスワード変更ビューのテスト"""

    def setUp(self) -> None:
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            is_email_verified=True,
        )
        self.client.login(username='test@example.com', password='testpass123')

    def test_password_change_page_loads(self) -> None:
        """パスワード変更ページの表示テスト"""
        response = self.client.get(reverse('password_change'))
        self.assertEqual(response.status_code, 200)

    def test_password_change_success(self) -> None:
        """パスワード変更成功テスト"""
        response = self.client.post(
            reverse('password_change'),
            {
                'old_password': 'testpass123',
                'new_password1': 'newpassword456',
                'new_password2': 'newpassword456',
            }
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword456'))

    def test_password_change_wrong_old_password(self) -> None:
        """旧パスワード不一致時のテスト"""
        response = self.client.post(
            reverse('password_change'),
            {
                'old_password': 'wrongpassword',
                'new_password1': 'newpassword456',
                'new_password2': 'newpassword456',
            }
        )
        self.assertEqual(response.status_code, 200)
