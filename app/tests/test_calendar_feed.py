"""
ICSカレンダー配信のテスト
"""
import uuid
from datetime import datetime, time, timedelta

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app.task.models import CalendarToken
from tests.factories import TaskFactory, UserFactory


def aware(day_offset: int, hour: int) -> datetime:
    base = timezone.localdate() + timedelta(days=day_offset)
    return timezone.make_aware(datetime.combine(base, time(hour, 0)))


@override_settings(
    SITE_DOMAIN='example.com',
    SITE_PROTOCOL='http',
    SITE_NAME='CarbohydratePro',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class CalendarFeedTest(TestCase):
    """ICSフィード配信のテスト"""

    def setUp(self) -> None:
        self.client = Client()
        self.user = UserFactory()
        self.token = CalendarToken.objects.create(user=self.user)

    def _feed_url(self, token: uuid.UUID | None = None) -> str:
        return reverse('calendar_feed', kwargs={'token': token or self.token.token})

    def test_feed_returns_ics(self) -> None:
        """有効なトークンでICSが返ること"""
        TaskFactory(user=self.user, title='会議', start_date=aware(1, 10), end_date=aware(1, 11))

        response = self.client.get(self._feed_url())
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/calendar', response['Content-Type'])
        content = response.content.decode('utf-8')
        self.assertIn('BEGIN:VCALENDAR', content)
        self.assertIn('SUMMARY:会議', content)
        self.assertIn('@example.com', content)
        self.assertIn('END:VCALENDAR', content)

    def test_invalid_token_returns_404(self) -> None:
        """無効なトークンは404になること"""
        response = self.client.get(self._feed_url(uuid.uuid4()))
        self.assertEqual(response.status_code, 404)

    def test_other_users_tasks_excluded(self) -> None:
        """他ユーザーのタスクは含まれないこと"""
        other = UserFactory()
        TaskFactory(user=other, title='他人の予定', start_date=aware(1, 10), end_date=aware(1, 11))

        content = self.client.get(self._feed_url()).content.decode('utf-8')
        self.assertNotIn('他人の予定', content)

    def test_all_day_event_uses_date_value(self) -> None:
        """終日タスクはDATE形式で翌日終了になること"""
        start = aware(2, 0)
        TaskFactory(user=self.user, title='終日イベント', start_date=start, end_date=start, all_day=True)

        content = self.client.get(self._feed_url()).content.decode('utf-8')
        start_str = timezone.localtime(start).date().strftime('%Y%m%d')
        end_str = (timezone.localtime(start).date() + timedelta(days=1)).strftime('%Y%m%d')
        self.assertIn(f'DTSTART;VALUE=DATE:{start_str}', content)
        self.assertIn(f'DTEND;VALUE=DATE:{end_str}', content)

    def test_special_characters_escaped(self) -> None:
        """カンマ・セミコロンがエスケープされること"""
        TaskFactory(user=self.user, title='買い物, 銀行; 郵便局', start_date=aware(1, 9), end_date=aware(1, 10))

        content = self.client.get(self._feed_url()).content.decode('utf-8')
        self.assertIn('SUMMARY:買い物\\, 銀行\\; 郵便局', content)

    def test_regenerate_invalidates_old_token(self) -> None:
        """再生成後は旧トークンが無効になること"""
        old_token = self.token.token
        self.token.regenerate()

        self.assertEqual(self.client.get(self._feed_url(old_token)).status_code, 404)
        self.assertEqual(self.client.get(self._feed_url(self.token.token)).status_code, 200)


@override_settings(
    SITE_DOMAIN='example.com',
    SITE_PROTOCOL='http',
    SITE_NAME='CarbohydratePro',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class CalendarSettingsTest(TestCase):
    """タスク設定画面のカレンダー連携UIのテスト"""

    def setUp(self) -> None:
        self.client = Client()
        self.user = UserFactory()
        self.client.login(username=self.user.email, password='testpass123')

    def test_settings_page_shows_feed_url(self) -> None:
        """設定画面に配信URLが表示され、トークンが自動作成されること"""
        response = self.client.get(reverse('task_settings'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'カレンダー連携')
        token = CalendarToken.objects.get(user=self.user)
        self.assertContains(response, f'/calendar/{token.token}.ics')

    def test_regenerate_via_settings(self) -> None:
        """設定画面からトークンを再生成できること"""
        self.client.get(reverse('task_settings'))
        old_token = CalendarToken.objects.get(user=self.user).token

        response = self.client.post(reverse('task_settings'), {'regenerate_calendar_token': '1'})
        self.assertEqual(response.status_code, 302)
        new_token = CalendarToken.objects.get(user=self.user).token
        self.assertNotEqual(old_token, new_token)
