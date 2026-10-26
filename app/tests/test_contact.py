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


class ContactHistoryTest(TestCase):
    """お問い合わせ履歴のページ切り替え・検索・詳細表示。"""

    def setUp(self) -> None:
        self.user = UserFactory()
        self.other = UserFactory()
        self.client.force_login(self.user)

    def _create(self, user: object, subject: str, message: str = "本文", inquiry_type: str = "feature") -> ContactMessage:
        return ContactMessage.objects.create(user=user, inquiry_type=inquiry_type, subject=subject, message=message)

    def test_history_is_paginated(self) -> None:
        for i in range(12):
            self._create(self.user, f"件名{i:02d}")
        first = self.client.get(reverse("contact"))
        self.assertEqual(len(first.context["user_messages"]), 10)
        self.assertTrue(first.context["page_obj"].has_next())
        second = self.client.get(reverse("contact"), {"page": 2})
        self.assertEqual(len(second.context["user_messages"]), 2)

    def test_search_matches_subject_or_message_and_keeps_filter_in_page_links(self) -> None:
        self._create(self.user, "家計簿グラフ", "配色を固定したい")
        self._create(self.user, "スケジュール", "月選択でカレンダーが出ない", inquiry_type="bug")
        for i in range(11):
            self._create(self.user, f"グラフ要望{i}")
        response = self.client.get(reverse("contact"), {"q": "カレンダー"})
        self.assertEqual([m.subject for m in response.context["user_messages"]], ["スケジュール"])

        response = self.client.get(reverse("contact"), {"q": "グラフ", "inquiry_type": "feature"})
        self.assertEqual(response.context["page_obj"].paginator.count, 12)
        self.assertContains(response, "&amp;q=%E3%82%B0%E3%83%A9%E3%83%95&amp;inquiry_type=feature")

    def test_search_does_not_include_other_users_messages(self) -> None:
        self._create(self.other, "他人の問い合わせ")
        response = self.client.get(reverse("contact"), {"q": "他人"})
        self.assertEqual(list(response.context["user_messages"]), [])
        self.assertNotContains(response, "他人の問い合わせ")

    def test_invalid_inquiry_type_filter_is_ignored(self) -> None:
        self._create(self.user, "残る")
        response = self.client.get(reverse("contact"), {"inquiry_type": "unknown"})
        self.assertEqual(response.context["inquiry_filter"], "")
        self.assertEqual(len(response.context["user_messages"]), 1)

    def test_detail_shows_full_message_with_line_breaks_and_reply(self) -> None:
        long_message = "1行目\n2行目 <script>alert(1)</script>\n" + "長い本文" * 100
        contact = self._create(self.user, "詳細確認", long_message)
        contact.admin_reply = "対応しました\n次回反映"
        contact.admin_reply_at = timezone.now()
        contact.save()

        history = self.client.get(reverse("contact"))
        self.assertContains(history, reverse("contact_detail", args=[contact.id]))

        response = self.client.get(reverse("contact_detail", args=[contact.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "長い本文" * 100)
        self.assertContains(response, "1行目\n2行目 &lt;script&gt;")
        self.assertContains(response, "対応しました\n次回反映")

    def test_detail_of_other_users_message_returns_404(self) -> None:
        contact = self._create(self.other, "他人")
        response = self.client.get(reverse("contact_detail", args=[contact.id]))
        self.assertEqual(response.status_code, 404)

    def test_detail_requires_login(self) -> None:
        contact = self._create(self.user, "自分")
        self.client.logout()
        response = self.client.get(reverse("contact_detail", args=[contact.id]))
        self.assertEqual(response.status_code, 302)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    SECURITY_ALERT_EMAIL="admin@example.com",
)
class ContactNotificationRecipientTest(TestCase):
    """お問い合わせ通知を開発用アドレスにも送る。"""

    def setUp(self) -> None:
        self.client.force_login(UserFactory())

    def _post(self) -> None:
        self.client.post(reverse("contact"), {"inquiry_type": "bug", "subject": "通知先", "message": "本文"})

    @override_settings(CONTACT_NOTIFICATION_EXTRA_EMAILS=["dev@example.com", " ", "admin@example.com"])
    def test_extra_addresses_are_added_without_duplicates(self) -> None:
        self._post()
        self.assertEqual(mail.outbox[-1].to, ["admin@example.com", "dev@example.com"])

    @override_settings(CONTACT_NOTIFICATION_EXTRA_EMAILS=[])
    def test_only_admin_when_extra_addresses_are_not_configured(self) -> None:
        self._post()
        self.assertEqual(mail.outbox[-1].to, ["admin@example.com"])
