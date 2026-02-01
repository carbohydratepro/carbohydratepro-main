from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    SITE_DOMAIN="example.com",
    SITE_PROTOCOL="http",
    SITE_NAME="CarbohydratePro",
    DEFAULT_FROM_EMAIL="no-reply@example.com",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class AuthTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.password = "test-pass-123"
        self.user = self.User.objects.create_user(
            email="user@example.com",
            username="tester",
            password=self.password,
            is_email_verified=True,
        )

    def test_login_success(self):
        """メールアドレスとパスワードでログインできる"""
        resp = self.client.post(
            reverse("login"), {"username": self.user.email, "password": self.password}
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue("_auth_user_id" in self.client.session)

    def test_login_invalid_credentials_shows_message(self):
        """誤った資格情報でログインすると日本語エラーメッセージが表示される"""
        resp = self.client.post(
            reverse("login"), {"username": self.user.email, "password": "wrong-pass"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "メールアドレスとパスワードが一致しません。")

    def test_signup_success_creates_user(self):
        """サインアップが成功し、ユーザーが作成されリダイレクトされる"""
        signup_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password1": "new-pass-123",
            "password2": "new-pass-123",
        }
        with patch("auth_app.views.EmailMultiAlternatives.send", return_value=None):
            resp = self.client.post(reverse("signup"), signup_data)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(self.User.objects.filter(email="new@example.com").exists())

    def test_signup_duplicate_username_message(self):
        """ユーザー名重複時に日本語メッセージが表示される"""
        signup_data = {
            "username": self.user.username,
            "email": "other@example.com",
            "password1": "some-pass-123",
            "password2": "some-pass-123",
        }
        resp = self.client.post(reverse("signup"), signup_data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "このユーザー名は使われています。")

    def test_signup_duplicate_email_message(self):
        """メールアドレス重複時に日本語メッセージが表示される"""
        signup_data = {
            "username": "anotheruser",
            "email": self.user.email,
            "password1": "some-pass-123",
            "password2": "some-pass-123",
        }
        resp = self.client.post(reverse("signup"), signup_data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "このメールアドレスは使われています。")
