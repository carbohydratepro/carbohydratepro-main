"""管理パネルのテスト"""
import json
from django.test import TestCase, Client
from django.urls import reverse

from app.models import ContactMessage
from tests.factories import UserFactory


def make_superuser() -> object:
    u = UserFactory()
    u.is_superuser = True
    u.is_staff = True
    u.is_email_verified = True
    u.save()
    return u


def make_staff_user() -> object:
    u = UserFactory()
    u.is_staff = True
    u.is_email_verified = True
    u.save()
    return u


def make_normal_user() -> object:
    u = UserFactory()
    u.is_email_verified = True
    u.save()
    return u


class ManageDashboardTest(TestCase):
    def setUp(self) -> None:
        self.superuser = make_superuser()
        self.staff_user = make_staff_user()
        self.normal_user = make_normal_user()
        self.client = Client()

    def test_dashboard_requires_login(self) -> None:
        response = self.client.get(reverse('manage_dashboard'))
        self.assertIn(response.status_code, [301, 302])

    def test_dashboard_blocked_for_normal_user(self) -> None:
        self.client.force_login(self.normal_user)
        response = self.client.get(reverse('manage_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_blocked_for_staff(self) -> None:
        """スタッフユーザーはアクセス不可"""
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('manage_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_accessible_to_superuser(self) -> None:
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('manage_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/manage/dashboard.html')


class ManageContactsTest(TestCase):
    def setUp(self) -> None:
        self.superuser = make_superuser()
        self.staff_user = make_staff_user()
        self.normal_user = make_normal_user()

        self.contact = ContactMessage.objects.create(
            user=self.normal_user,
            inquiry_type='bug',
            subject='テスト',
            message='バグがあります',
            status='open',
        )
        self.client = Client()

    def test_contacts_blocked_for_staff(self) -> None:
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('manage_contacts'))
        self.assertEqual(response.status_code, 403)

    def test_contacts_blocked_for_normal(self) -> None:
        self.client.force_login(self.normal_user)
        response = self.client.get(reverse('manage_contacts'))
        self.assertEqual(response.status_code, 403)

    def test_contacts_accessible_to_superuser(self) -> None:
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('manage_contacts'))
        self.assertEqual(response.status_code, 200)

    def test_contacts_filter_by_status(self) -> None:
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('manage_contacts') + '?status=open')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.contact, response.context['contacts'])

    def test_update_contact_status(self) -> None:
        self.client.force_login(self.superuser)
        self.client.post(
            reverse('manage_contact_update', args=[self.contact.id]),
            {'status': 'in_progress'},
        )
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.status, 'in_progress')

    def test_update_contact_blocked_for_staff(self) -> None:
        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse('manage_contact_update', args=[self.contact.id]),
            {'status': 'resolved'},
        )
        self.assertEqual(response.status_code, 403)
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.status, 'open')

    def test_update_contact_with_reply(self) -> None:
        self.client.force_login(self.superuser)
        self.client.post(
            reverse('manage_contact_update', args=[self.contact.id]),
            {'status': 'resolved', 'admin_reply': '対応しました'},
        )
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.status, 'resolved')
        self.assertEqual(self.contact.admin_reply, '対応しました')
        self.assertIsNotNone(self.contact.admin_reply_at)

    def test_cannot_update_with_invalid_status(self) -> None:
        self.client.force_login(self.superuser)
        self.client.post(
            reverse('manage_contact_update', args=[self.contact.id]),
            {'status': 'invalid_status'},
        )
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.status, 'open')


class ManageUsersTest(TestCase):
    def setUp(self) -> None:
        self.superuser = make_superuser()
        self.staff_user = make_staff_user()
        self.client = Client()

    def test_users_blocked_for_staff(self) -> None:
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('manage_users'))
        self.assertEqual(response.status_code, 403)

    def test_users_accessible_to_superuser(self) -> None:
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('manage_users'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/manage/users.html')

    def test_stats_api_blocked_for_staff(self) -> None:
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('manage_users_stats_api'))
        self.assertEqual(response.status_code, 403)

    def test_stats_api_returns_json(self) -> None:
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('manage_users_stats_api'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('labels', data)
        self.assertIn('new_counts', data)
        self.assertIn('total_counts', data)

    def test_stats_api_monthly(self) -> None:
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('manage_users_stats_api') + '?period=monthly&days=90')
        self.assertEqual(response.status_code, 200)

    def test_stats_api_verified_only(self) -> None:
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('manage_users_stats_api') + '?verified_only=1')
        self.assertEqual(response.status_code, 200)
