"""
外部カレンダー（ICS購読）のテスト
"""
from datetime import datetime, time, timedelta
from unittest.mock import MagicMock, patch

from django.test import Client, TestCase
from django.utils import timezone

from app.home_views import build_dashboard_context
from app.task import services
from app.task.models import ExternalCalendar, ExternalEvent
from tests.factories import UserFactory


def build_test_ics(base_date: datetime) -> bytes:
    """テスト用ICS（時間指定・終日・週次繰り返し）を生成する。"""
    day = base_date.strftime('%Y%m%d')
    next_day = (base_date + timedelta(days=1)).strftime('%Y%m%d')
    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Test//Test//EN',
        'BEGIN:VEVENT',
        'UID:single-1',
        f'DTSTART;TZID=Asia/Tokyo:{day}T100000',
        f'DTEND;TZID=Asia/Tokyo:{day}T110000',
        'SUMMARY:歯科検診',
        'END:VEVENT',
        'BEGIN:VEVENT',
        'UID:allday-1',
        f'DTSTART;VALUE=DATE:{day}',
        f'DTEND;VALUE=DATE:{next_day}',
        'SUMMARY:資源ごみの日',
        'END:VEVENT',
        'BEGIN:VEVENT',
        'UID:weekly-1',
        f'DTSTART;TZID=Asia/Tokyo:{day}T190000',
        f'DTEND;TZID=Asia/Tokyo:{day}T200000',
        'RRULE:FREQ=WEEKLY;COUNT=3',
        'SUMMARY:ジム',
        'END:VEVENT',
        'END:VCALENDAR',
    ]
    return '\r\n'.join(lines).encode('utf-8')


class UrlValidationTest(TestCase):
    """URL正規化とSSRF対策のテスト"""

    def test_webcal_is_converted_to_https(self) -> None:
        """webcal:// は https:// に変換されること"""
        url = services.normalize_external_calendar_url('webcal://example.com/cal.ics')
        self.assertEqual(url, 'https://example.com/cal.ics')

    def test_invalid_scheme_is_rejected(self) -> None:
        """http/https 以外のスキームは拒否されること"""
        for bad_url in ['ftp://example.com/cal.ics', 'file:///etc/passwd', 'example.com/cal.ics']:
            with self.assertRaises(ValueError):
                services.normalize_external_calendar_url(bad_url)

    def test_private_hosts_are_rejected(self) -> None:
        """プライベート/ループバック/メタデータIPへのアクセスは拒否されること"""
        for host in ['127.0.0.1', '10.0.0.1', '192.168.1.1', '169.254.169.254', 'localhost']:
            with self.assertRaises(ValueError):
                services._assert_public_host(host)

    def test_public_host_is_allowed(self) -> None:
        """グローバルIPは許可されること"""
        services._assert_public_host('8.8.8.8')  # 例外が出ないこと

    def test_redirect_to_private_host_is_rejected(self) -> None:
        """リダイレクト先がプライベートIPの場合は拒否されること"""
        redirect_response = MagicMock()
        redirect_response.is_redirect = True
        redirect_response.is_permanent_redirect = False
        redirect_response.headers = {'Location': 'http://127.0.0.1/steal'}
        with patch('requests.get', return_value=redirect_response):
            with self.assertRaises(ValueError):
                services.fetch_external_ics('https://93.184.216.34/cal.ics')


class SyncExternalCalendarTest(TestCase):
    """同期処理のテスト"""

    def setUp(self) -> None:
        self.user = UserFactory()
        self.calendar = ExternalCalendar.objects.create(
            user=self.user, name='テストカレンダー',
            url='https://example.com/cal.ics', color='#4285f4',
        )
        tomorrow = timezone.localdate() + timedelta(days=1)
        self.base_date = datetime.combine(tomorrow, time.min)

    def test_sync_creates_events_with_rrule_expansion(self) -> None:
        """時間指定・終日・RRULE展開を含むイベントが取り込まれること"""
        ics = build_test_ics(self.base_date)
        with patch('app.task.services.fetch_external_ics', return_value=ics):
            count = services.sync_external_calendar(self.calendar)

        # 単発1 + 終日1 + 週次3回 = 5件
        self.assertEqual(count, 5)
        self.assertEqual(self.calendar.events.count(), 5)

        allday = self.calendar.events.get(uid='allday-1')
        self.assertTrue(allday.all_day)
        self.assertEqual(timezone.localtime(allday.start_date).date(), self.base_date.date())
        # 排他的DTENDが包含に変換されている（同日終わり）
        self.assertEqual(timezone.localtime(allday.end_date).date(), self.base_date.date())

        timed = self.calendar.events.get(uid='single-1')
        self.assertFalse(timed.all_day)
        self.assertEqual(timezone.localtime(timed.start_date).hour, 10)

        self.assertEqual(self.calendar.events.filter(uid='weekly-1').count(), 3)

        self.calendar.refresh_from_db()
        self.assertIsNotNone(self.calendar.last_synced_at)
        self.assertEqual(self.calendar.last_error, '')

    def test_sync_replaces_existing_events(self) -> None:
        """再同期でイベントが洗い替えされ重複しないこと"""
        ics = build_test_ics(self.base_date)
        with patch('app.task.services.fetch_external_ics', return_value=ics):
            services.sync_external_calendar(self.calendar)
            services.sync_external_calendar(self.calendar)
        self.assertEqual(self.calendar.events.count(), 5)

    def test_sync_failure_records_error_and_keeps_events(self) -> None:
        """同期失敗時はエラーを記録し、既存イベントを保持すること"""
        ics = build_test_ics(self.base_date)
        with patch('app.task.services.fetch_external_ics', return_value=ics):
            services.sync_external_calendar(self.calendar)

        with patch('app.task.services.fetch_external_ics', side_effect=ValueError('接続エラー')):
            success, message = services.sync_external_calendar_safe(self.calendar)

        self.assertFalse(success)
        self.assertIn('接続エラー', message)
        self.calendar.refresh_from_db()
        self.assertEqual(self.calendar.last_error, '接続エラー')
        self.assertEqual(self.calendar.events.count(), 5)


class ExternalCalendarViewTest(TestCase):
    """タスク設定画面の外部カレンダー管理のテスト"""

    def setUp(self) -> None:
        self.user = UserFactory()
        self.client = Client()
        self.client.force_login(self.user)

    def test_settings_page_shows_external_calendar_section(self) -> None:
        """設定画面に外部カレンダーセクションが表示されること"""
        response = self.client.get('/carbohydratepro/tasks/settings/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '外部カレンダーの取り込み')

    def test_add_external_calendar(self) -> None:
        """外部カレンダーを追加すると即時同期されること"""
        with patch('app.task.services.sync_external_calendar_safe', return_value=(True, '5件のイベントを取り込みました。')) as mock_sync:
            response = self.client.post('/carbohydratepro/tasks/settings/', {
                'add_external_calendar': '1',
                'name': 'Googleカレンダー',
                'url': 'webcal://calendar.google.com/calendar/ical/test/basic.ics',
                'color': '#4285f4',
            })
        self.assertRedirects(response, '/carbohydratepro/tasks/settings/')
        calendar = ExternalCalendar.objects.get(user=self.user)
        self.assertEqual(calendar.name, 'Googleカレンダー')
        # webcal:// が https:// に正規化されている
        self.assertTrue(calendar.url.startswith('https://'))
        mock_sync.assert_called_once()

    def test_add_duplicate_url_is_rejected(self) -> None:
        """同じURLの二重登録はエラーになること"""
        ExternalCalendar.objects.create(
            user=self.user, name='既存', url='https://example.com/cal.ics',
        )
        with patch('app.task.services.sync_external_calendar_safe', return_value=(True, '')):
            self.client.post('/carbohydratepro/tasks/settings/', {
                'add_external_calendar': '1',
                'name': '重複',
                'url': 'https://example.com/cal.ics',
                'color': '#4285f4',
            })
        self.assertEqual(ExternalCalendar.objects.filter(user=self.user).count(), 1)

    def test_invalid_url_is_rejected(self) -> None:
        """不正なスキームのURLは登録できないこと"""
        self.client.post('/carbohydratepro/tasks/settings/', {
            'add_external_calendar': '1',
            'name': '不正',
            'url': 'ftp://example.com/cal.ics',
            'color': '#4285f4',
        })
        self.assertEqual(ExternalCalendar.objects.count(), 0)

    def test_delete_external_calendar(self) -> None:
        """外部カレンダーを削除できること"""
        calendar = ExternalCalendar.objects.create(
            user=self.user, name='削除対象', url='https://example.com/cal.ics',
        )
        self.client.post('/carbohydratepro/tasks/settings/', {
            'delete_external_calendar': '1',
            'external_calendar_id': calendar.id,
        })
        self.assertEqual(ExternalCalendar.objects.count(), 0)

    def test_cannot_manage_other_users_calendar(self) -> None:
        """他ユーザーの外部カレンダーは操作できないこと"""
        other_calendar = ExternalCalendar.objects.create(
            user=UserFactory(), name='他人の', url='https://example.com/other.ics',
        )
        response = self.client.post('/carbohydratepro/tasks/settings/', {
            'delete_external_calendar': '1',
            'external_calendar_id': other_calendar.id,
        })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(ExternalCalendar.objects.count(), 1)


class ExternalEventDisplayTest(TestCase):
    """外部イベントの表示統合のテスト"""

    def setUp(self) -> None:
        self.user = UserFactory()
        self.client = Client()
        self.client.force_login(self.user)
        self.calendar = ExternalCalendar.objects.create(
            user=self.user, name='Google', url='https://example.com/cal.ics', color='#4285f4',
        )
        today = timezone.localdate()
        start = timezone.make_aware(datetime.combine(today, time(15, 0)))
        self.event = ExternalEvent.objects.create(
            calendar=self.calendar,
            uid='ev-1',
            title='外部の打ち合わせ',
            start_date=start,
            end_date=start + timedelta(hours=1),
            all_day=False,
        )

    def test_dashboard_includes_external_events(self) -> None:
        """ダッシュボードの今日のタスクに外部イベントが含まれること"""
        context = build_dashboard_context(self.user)
        titles = [item.title for item in context['today_tasks']]
        self.assertIn('外部の打ち合わせ', titles)
        self.assertEqual(context['today_tasks_count'], 1)

    def test_day_api_includes_external_events(self) -> None:
        """日別タスクAPIに外部イベントが読み取り専用で含まれること"""
        today = timezone.localdate().strftime('%Y-%m-%d')
        response = self.client.get(f'/carbohydratepro/tasks/day/{today}/')
        data = response.json()
        self.assertTrue(data['success'])
        external = [t for t in data['tasks'] if t.get('is_external')]
        self.assertEqual(len(external), 1)
        self.assertEqual(external[0]['title'], '外部の打ち合わせ')
        self.assertEqual(external[0]['calendar']['color'], '#4285f4')

    def test_month_view_shows_external_events(self) -> None:
        """月カレンダーに外部イベントが表示されること"""
        response = self.client.get('/carbohydratepro/tasks/?view_mode=month')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '外部の打ち合わせ')
        self.assertContains(response, 'external-event')

    def test_day_view_shows_external_events_without_edit(self) -> None:
        """日表示ガントに外部イベントが編集リンクなしで表示されること"""
        today = timezone.localdate().strftime('%Y-%m-%d')
        response = self.client.get(f'/carbohydratepro/tasks/?view_mode=day&target_date={today}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '外部の打ち合わせ')
        self.assertContains(response, 'gantt-bar-external')
        # 外部イベントには編集モーダルのonclickが付かない
        content = response.content.decode('utf-8')
        self.assertNotIn(f'openEditTaskModal({self.event.id})', content)
