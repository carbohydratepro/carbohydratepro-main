"""速報・収集・管理画面の回帰。外部メールや実データは使わない。"""
import json
import logging
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone

from auth_app.security_collection import collect_events
from auth_app.security_models import SecurityAlertState, SecurityEvent, SecurityMonitorState
from auth_app.security_notifications import send_urgent_report
from auth_app.security_rules import parse_application_line
from project.logging_filters import PlannedMaintenanceFilter
from tests.factories import UserFactory


@override_settings(SECURITY_HOST_MONITOR_ENABLED=False, SEND_URGENT_SECURITY_EMAIL=True,
                   EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class SecurityMonitoringTest(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.now = timezone.now()

    def event(self, category='app_critical', severity='critical', seconds=1):
        return SecurityEvent.objects.create(fingerprint=str(SecurityEvent.objects.count()),
            occurred_at=self.now-timedelta(seconds=seconds), source='app', category=category,
            severity=severity, summary='分類済みの要約')

    def test_rotation_does_not_duplicate_and_private_text_not_stored(self):
        stamp = timezone.localtime(self.now).strftime('%Y-%m-%d %H:%M:%S')
        line = f'ERROR {stamp},000 views 1 1 password=private-value person@example.com\n'
        path = self.root/'django_debug.log'
        path.write_text(line+line)
        with override_settings(BASE_DIR=self.root):
            collect_events(self.now)
            path.rename(self.root/'django_debug.log.1')
            path.write_text('')
            collect_events(self.now+timedelta(minutes=2))
        self.assertEqual(SecurityEvent.objects.count(), 2)
        self.assertNotIn('private-value', str(list(SecurityEvent.objects.values())))
        self.assertNotIn('person@example.com', str(list(SecurityEvent.objects.values())))

    def test_only_critical_and_error_bursts_are_urgent(self):
        self.event('privileged_login', 'warning')
        self.event('admin_probe', 'warning')
        self.event('maintenance', 'info')
        for _ in range(9): self.event('app_error', 'error')
        self.assertFalse(send_urgent_report(self.now))
        self.event('app_error', 'error')
        self.assertTrue(send_urgent_report(self.now))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('5分間に10件', mail.outbox[0].body)

    def test_one_digest_and_cooldown_without_resending_old_events(self):
        self.event()
        self.event('file_integrity')
        self.assertTrue(send_urgent_report(self.now))
        self.assertFalse(send_urgent_report(self.now+timedelta(minutes=2)))
        self.assertFalse(send_urgent_report(self.now+timedelta(hours=2)))
        self.now += timedelta(minutes=30)
        self.event()
        self.assertFalse(send_urgent_report(self.now))
        self.assertTrue(send_urgent_report(self.now+timedelta(minutes=31)))
        self.assertEqual(len(mail.outbox), 2)

    def test_smtp_failure_is_retried_without_claiming_delivery(self):
        self.event()
        with patch('auth_app.security_notifications.send_mail', side_effect=RuntimeError('failed')):
            with self.assertRaises(RuntimeError): send_urgent_report(self.now)
        self.assertIsNone(SecurityAlertState.objects.get(signature='app_critical').sent_at)
        self.assertTrue(send_urgent_report(self.now+timedelta(minutes=2)))

    def test_initial_backfill_is_not_urgently_sent(self):
        self.event(seconds=3600)
        self.assertFalse(send_urgent_report(self.now))
        self.event()
        self.assertTrue(send_urgent_report(self.now))
        self.assertIn('1件', mail.outbox[0].body)
        self.assertNotIn('2件', mail.outbox[0].body)

    def test_late_arriving_critical_is_not_lost_after_an_earlier_send(self):
        self.event()
        self.assertTrue(send_urgent_report(self.now))
        self.event(seconds=60)
        self.assertTrue(send_urgent_report(self.now+timedelta(minutes=61)))
        self.assertIn('1件', mail.outbox[-1].body)

    def test_url_or_log_text_cannot_disguise_real_errors(self):
        for text in ['Internal Server Error: /csrf/forbidden/', 'Failure: Planned maintenance response']:
            parsed = parse_application_line('ERROR 2026-11-01 10:00:00,000 log 1 1 '+text, 'app')
            self.assertEqual(parsed[1:], ('app_error', 'error'))

    def test_noise_is_not_critical_even_if_logger_says_so(self):
        parsed = parse_application_line('CRITICAL 2026-11-01 10:00:00,000 middleware 1 1 Suspicious access attempt /wp-admin/', 'security')
        self.assertEqual(parsed[1:], ('admin_probe', 'warning'))

    def test_only_explicit_planned_503_is_downgraded(self):
        request = RequestFactory().get('/login/')
        record = logging.LogRecord('django.request', logging.ERROR, '', 0, 'Service Unavailable: %s', ('/login/',), None)
        record.status_code = 503
        record.request = request
        filter_ = PlannedMaintenanceFilter()
        filter_.filter(record)
        self.assertEqual(record.levelno, logging.ERROR)
        request._planned_maintenance_response = True
        filter_.filter(record)
        self.assertEqual(record.levelno, logging.INFO)
        self.assertEqual(record.getMessage(), 'Planned maintenance response')

    @override_settings(SECURITY_HOST_MONITOR_ENABLED=True)
    def test_stopped_host_monitor_is_urgent(self):
        self.assertTrue(send_urgent_report(self.now))
        self.assertIn('監視の更新停止', mail.outbox[0].body)
        self.assertFalse(send_urgent_report(self.now+timedelta(minutes=2)))

    def test_disabled_mail_still_collects_events(self):
        stamp = timezone.localtime(self.now).strftime('%Y-%m-%d %H:%M:%S')
        (self.root/'django_debug.log').write_text(f'ERROR {stamp},000 views 1 1 sample\n')
        with override_settings(BASE_DIR=self.root, SEND_PERIODIC_SECURITY_EMAIL=False):
            call_command('check_security_log')
        self.assertEqual(SecurityEvent.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_dashboard_privacy_and_zero_vs_uncollected(self):
        self.event()
        for staff, superuser, expected in [(False, False, 403), (True, False, 403), (True, True, 200)]:
            user = UserFactory(is_staff=staff, is_superuser=superuser)
            self.client.force_login(user)
            response = self.client.get(reverse('manage_dashboard'))
            self.assertEqual(response.status_code, expected)
        self.assertContains(response, 'security-chart')
        self.assertTrue(response.context['security']['stale'])
        self.assertIsNone(response.context['security']['days'][-1]['critical'])
        SecurityMonitorState.objects.create(name='application', started_at=self.now-timedelta(days=1), checked_at=self.now)
        response = self.client.get(reverse('manage_dashboard'))
        self.assertEqual(response.context['security']['days'][-1]['critical'], 1)
        self.assertEqual(response.context['security']['days'][-2]['critical'], 0)
        self.assertIsNone(response.context['security']['days'][0]['critical'])
        self.client.logout()
        self.assertEqual(self.client.get(reverse('manage_dashboard')).status_code, 302)

    @override_settings(SECURITY_HOST_MONITOR_ENABLED=True)
    def test_host_events_are_validated_and_rotation_is_idempotent(self):
        stamp = self.now.isoformat()
        (self.root/'heartbeat.json').write_text(json.dumps({'checked_at': stamp, 'healthy': True}))
        path = self.root/'events.jsonl'
        path.write_text(json.dumps({'id': 'stable-id', 'occurred_at': stamp,
                                    'category': 'file_integrity', 'detail': 'do-not-copy'})+'\n')
        with override_settings(BASE_DIR=self.root, SECURITY_HOST_MONITOR_DIR=self.root):
            collect_events(self.now)
            path.rename(self.root/'events.jsonl.1')
            path.write_text('')
            collect_events(self.now+timedelta(minutes=1))
            self.assertEqual(SecurityEvent.objects.count(), 1)
            self.assertNotIn('do-not-copy', str(list(SecurityEvent.objects.values())))
            self.assertEqual(SecurityEvent.objects.get().severity, 'critical')
            (self.root/'heartbeat.json').write_text('not-json')
            with self.assertRaises(ValueError): collect_events(self.now+timedelta(minutes=2))
            self.assertTrue(SecurityMonitorState.objects.get(name='application').error)

    @override_settings(SECURITY_HOST_MONITOR_ENABLED=True)
    def test_host_backlog_survives_application_collection_advancing(self):
        SecurityMonitorState.objects.create(name='application', checked_at=self.now-timedelta(minutes=2))
        SecurityMonitorState.objects.create(name='notifications', started_at=self.now-timedelta(hours=2))
        (self.root/'heartbeat.json').write_text(json.dumps({'checked_at': self.now.isoformat(), 'healthy': True}))
        (self.root/'events.jsonl').write_text(json.dumps({'id': 'late-host-event',
            'occurred_at': (self.now-timedelta(hours=1)).isoformat(), 'category': 'ssh_unexpected_login'})+'\n')
        with override_settings(BASE_DIR=self.root, SECURITY_HOST_MONITOR_DIR=self.root):
            collect_events(self.now)
        self.assertEqual(SecurityEvent.objects.count(), 1)
        self.assertTrue(send_urgent_report(self.now))
        self.assertIn('許可範囲外', mail.outbox[0].body)

    def test_no_urgent_email_for_a_single_planned_maintenance(self):
        stamp = timezone.localtime(self.now).strftime('%Y-%m-%d %H:%M:%S')
        (self.root/'django_debug.log').write_text(f'INFO {stamp},000 log 1 1 Planned maintenance response\n')
        with override_settings(BASE_DIR=self.root):
            call_command('check_security_log', urgent=True)
        self.assertEqual(SecurityEvent.objects.get().category, 'maintenance')
        self.assertEqual(len(mail.outbox), 0)
