"""お問い合わせ通知メールの日時表示。"""
from datetime import datetime, timezone as datetime_timezone
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.models import ContactMessage
from tests.factories import UserFactory


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ContactMailTimezoneTest(TestCase):
    def setUp(self) -> None:
        self.user = UserFactory(is_email_verified=True)
        self.client.force_login(self.user)

    def test_notification_uses_japan_time_without_changing_stored_instant(self) -> None:
        cases = [
            (datetime(2026, 10, 12, 9, 8, 53, tzinfo=datetime_timezone.utc), "2026年10月12日 18:08:53"),
            (datetime(2026, 10, 12, 15, 0, 0, tzinfo=datetime_timezone.utc), "2026年10月13日 00:00:00"),
        ]
        for instant, expected in cases:
            with self.subTest(instant=instant), timezone.override("UTC"):
                with patch("django.utils.timezone.now", return_value=instant):
                    response = self.client.post(reverse("contact"), {
                        "inquiry_type": "bug",
                        "subject": "日時表示の確認",
                        "message": "複数行の本文\n特殊文字 <> &",
                    })
                self.assertRedirects(response, reverse("contact"))
                self.assertIn(f"送信日時: {expected}（日本時間）", mail.outbox[-1].body)
                self.assertIn("複数行の本文\n特殊文字 <> &", mail.outbox[-1].body)
                saved = ContactMessage.objects.filter(user=self.user).order_by("-pk").first()
                self.assertIsNotNone(saved)
                self.assertEqual(saved.created_at, instant)
        self.assertEqual(len(mail.outbox), len(cases))
