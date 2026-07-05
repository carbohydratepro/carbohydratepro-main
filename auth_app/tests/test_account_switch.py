from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from auth_app import services
from auth_app.forms import UserUpdateForm
from auth_app.models import AccountGroupLink, AccountMembership


def create_user(
    username: str = 'test-user',
    email: str = 'user@example.com',
    password: str = 'testpass123',
    is_email_verified: bool = True,
):
    return get_user_model().objects.create_user(
        username=username,
        email=email,
        password=password,
        is_active=True,
        is_email_verified=is_email_verified,
    )


@override_settings(
    SITE_DOMAIN='example.com',
    SITE_PROTOCOL='http',
    SITE_NAME='CarbohydratePro',
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class AccountSwitchViewTest(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.password = 'testpass123'
        self.user = create_user(username='main-user', email='main@example.com', password=self.password)
        self.other_user = create_user(username='other-user', email='other@example.com', password=self.password)
        self.third_user = create_user(username='third-user', email='third@example.com', password=self.password)
        self.client.login(username=self.user.email, password=self.password)

    def test_login_creates_account_group(self) -> None:
        self.assertTrue(AccountMembership.objects.filter(user=self.user).exists())
        session = self.client.session
        self.assertIn(services.ACCOUNT_GROUP_SESSION_KEY, session)
        self.assertIn(self.user.pk, session[services.ACCOUNT_ACTIVE_USER_IDS_SESSION_KEY])

    def test_add_existing_account_links_and_switches(self) -> None:
        response = self.client.post(
            reverse('account_add'),
            {
                'form_type': 'existing',
                'existing-email': self.other_user.email,
                'existing-password': self.password,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.other_user.pk)
        # グループは合流せず、親子リンクが作られる
        self.assertNotEqual(
            self.user.account_membership.group_id,
            self.other_user.account_membership.group_id,
        )
        self.assertTrue(
            AccountGroupLink.objects.filter(
                parent=self.user.account_membership.group,
                child=self.other_user.account_membership.group,
            ).exists()
        )

    def test_unverified_account_cannot_be_added(self) -> None:
        self.other_user.is_email_verified = False
        self.other_user.save(update_fields=['is_email_verified'])

        response = self.client.post(
            reverse('account_add'),
            {
                'form_type': 'existing',
                'existing-email': self.other_user.email,
                'existing-password': self.password,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'メール認証が完了していないアカウントは追加できません。')

    def test_new_account_creation_is_not_available_on_account_add(self) -> None:
        get_response = self.client.get(reverse('account_add'))
        self.assertContains(get_response, '既存アカウントを追加')
        self.assertNotContains(get_response, '新規アカウントを作成')

        response = self.client.post(
            reverse('account_add'),
            {
                'form_type': 'new',
                'new-username': 'linked-user',
                'new-email': 'linked@example.com',
                'new-password1': 'linked-password-123',
                'new-password2': 'linked-password-123',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '既存アカウントを追加')
        self.assertFalse(get_user_model().objects.filter(email='linked@example.com').exists())

    def test_add_account_linked_elsewhere_does_not_expose_other_links(self) -> None:
        # other_user は third_user を既に連携済み（other が親、third が子）
        services.link_accounts(self.other_user, self.third_user, created_by=self.other_user)

        response = self.client.post(
            reverse('account_add'),
            {
                'form_type': 'existing',
                'existing-email': self.other_user.email,
                'existing-password': self.password,
            },
        )

        # 連携は成功し other_user に切り替わる
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.other_user.pk)

        # user から見ると other は切替候補だが、other の子（孫にあたる third）は見えない
        user_related = {
            membership.user_id
            for membership in services.get_related_memberships(self.user.account_membership.group)
        }
        self.assertEqual(user_related, {self.user.pk, self.other_user.pk})

        # other から見ると親（user）と子（third）の両方が切替候補
        other_related = {
            membership.user_id
            for membership in services.get_related_memberships(self.other_user.account_membership.group)
        }
        self.assertEqual(other_related, {self.user.pk, self.other_user.pk, self.third_user.pk})

    def test_siblings_under_same_parent_can_switch_mutually(self) -> None:
        # user が other と third を追加すると、兄弟同士も相互に切替候補になる
        services.link_accounts(self.user, self.other_user, created_by=self.user)
        services.link_accounts(self.user, self.third_user, created_by=self.user)

        other_related = {
            membership.user_id
            for membership in services.get_related_memberships(self.other_user.account_membership.group)
        }
        self.assertEqual(other_related, {self.user.pk, self.other_user.pk, self.third_user.pk})

    def test_child_with_multiple_parents_does_not_cross_families(self) -> None:
        # other は user と third の両方の子になれる（複数グループへの所属）
        services.link_accounts(self.user, self.other_user, created_by=self.user)
        services.link_accounts(self.third_user, self.other_user, created_by=self.third_user)

        # other からは両方のファミリーが見える
        other_related = {
            membership.user_id
            for membership in services.get_related_memberships(self.other_user.account_membership.group)
        }
        self.assertEqual(other_related, {self.user.pk, self.other_user.pk, self.third_user.pk})

        # user と third は other を介してつながらない
        user_related = {
            membership.user_id
            for membership in services.get_related_memberships(self.user.account_membership.group)
        }
        self.assertEqual(user_related, {self.user.pk, self.other_user.pk})
        third_related = {
            membership.user_id
            for membership in services.get_related_memberships(self.third_user.account_membership.group)
        }
        self.assertEqual(third_related, {self.third_user.pk, self.other_user.pk})

    def test_current_account_logout_switches_to_next_and_requires_login_only_for_logged_out_account(self) -> None:
        group = services.link_accounts(self.user, self.other_user, created_by=self.user)
        services.link_accounts(self.user, self.third_user, created_by=self.user)
        session = self.client.session
        session[services.ACCOUNT_GROUP_SESSION_KEY] = group.pk
        session[services.ACCOUNT_ACTIVE_USER_IDS_SESSION_KEY] = [
            self.user.pk,
            self.other_user.pk,
            self.third_user.pk,
        ]
        session.save()

        response = self.client.post(reverse('logout'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.other_user.pk)
        active_user_ids = self.client.session[services.ACCOUNT_ACTIVE_USER_IDS_SESSION_KEY]
        self.assertNotIn(self.user.pk, active_user_ids)
        self.assertIn(self.other_user.pk, active_user_ids)
        self.assertIn(self.third_user.pk, active_user_ids)

        edit_response = self.client.get(reverse('account_edit'))
        self.assertContains(edit_response, self.user.email)
        self.assertContains(edit_response, self.other_user.email)
        self.assertContains(edit_response, self.third_user.email)
        self.assertContains(edit_response, 'ログアウト済み')

        switch_response = self.client.post(reverse('account_switch', kwargs={'pk': self.third_user.pk}))
        self.assertEqual(switch_response.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.third_user.pk)
        active_user_ids = self.client.session[services.ACCOUNT_ACTIVE_USER_IDS_SESSION_KEY]
        self.assertNotIn(self.user.pk, active_user_ids)
        self.assertIn(self.other_user.pk, active_user_ids)
        self.assertIn(self.third_user.pk, active_user_ids)

        logged_out_switch_response = self.client.post(reverse('account_switch', kwargs={'pk': self.user.pk}))
        self.assertEqual(logged_out_switch_response.status_code, 302)
        self.assertTrue(logged_out_switch_response.url.startswith(reverse('login')))
        query = parse_qs(urlparse(logged_out_switch_response.url).query)
        self.assertEqual(query['email'], [self.user.email])
        self.assertEqual(query['account_switch'], ['1'])
        self.assertEqual(int(self.client.session['_auth_user_id']), self.third_user.pk)

        login_response = self.client.get(logged_out_switch_response.url)
        self.assertContains(login_response, f'value="{self.user.email}"')

        login_response = self.client.post(
            logged_out_switch_response.url,
            {'username': self.user.email, 'password': self.password, 'next': reverse('top')},
        )
        self.assertEqual(login_response.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)
        active_user_ids = self.client.session[services.ACCOUNT_ACTIVE_USER_IDS_SESSION_KEY]
        self.assertIn(self.user.pk, active_user_ids)
        self.assertIn(self.other_user.pk, active_user_ids)
        self.assertIn(self.third_user.pk, active_user_ids)

    def test_remove_only_other_account(self) -> None:
        group = services.link_accounts(self.user, self.other_user, created_by=self.user)
        session = self.client.session
        session[services.ACCOUNT_GROUP_SESSION_KEY] = group.pk
        session[services.ACCOUNT_ACTIVE_USER_IDS_SESSION_KEY] = [self.user.pk, self.other_user.pk]
        session.save()

        edit_response = self.client.get(reverse('account_edit'))
        self.assertContains(edit_response, 'アカウント編集')
        self.assertContains(edit_response, "confirm('このアカウントの連携を解除しますか？');")

        response = self.client.post(reverse('account_remove', kwargs={'pk': self.other_user.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('account_edit'))
        # 解除後は切替候補から消える（親子リンクが削除される）
        user_related = {
            membership.user_id
            for membership in services.get_related_memberships(self.user.account_membership.group)
        }
        self.assertNotIn(self.other_user.pk, user_related)
        self.assertFalse(AccountGroupLink.objects.exists())

        response = self.client.post(reverse('account_remove', kwargs={'pk': self.user.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('account_edit'))
        self.assertEqual(AccountMembership.objects.filter(user=self.user).count(), 1)

    def test_remove_legacy_same_group_member(self) -> None:
        # 旧仕様データ（同一グループ所属）は対象を新しいグループへ分離する
        group = services.ensure_account_group(self.user)
        services.ensure_account_group(self.other_user)
        AccountMembership.objects.filter(user=self.other_user).update(group=group)

        # リレーションキャッシュを避けるため再取得する
        other_user = get_user_model().objects.get(pk=self.other_user.pk)
        self.assertTrue(services.remove_account_from_group(self.user, other_user))
        other_user = get_user_model().objects.get(pk=self.other_user.pk)
        self.assertNotEqual(
            self.user.account_membership.group_id,
            other_user.account_membership.group_id,
        )


class AvatarValidationTest(TestCase):
    def test_avatar_accepts_small_png(self) -> None:
        user = create_user()
        png_file = SimpleUploadedFile(
            'avatar.png',
            b'\x89PNG\r\n\x1a\n' + b'\x00' * 20,
            content_type='image/png',
        )

        form = UserUpdateForm(
            data={'username': user.username, 'email': user.email},
            files={'avatar': png_file},
            instance=user,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_avatar_rejects_unknown_content(self) -> None:
        user = create_user()
        invalid_file = SimpleUploadedFile(
            'avatar.png',
            b'not an image',
            content_type='image/png',
        )

        form = UserUpdateForm(
            data={'username': user.username, 'email': user.email},
            files={'avatar': invalid_file},
            instance=user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('avatar', form.errors)
