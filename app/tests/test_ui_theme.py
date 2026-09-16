"""管理系も通常画面と同じUI資産を使う。権限検証は既存test_manageと併用する。"""
from django.test import TestCase
from django.templatetags.static import static
from django.urls import reverse

from app.models import ContactMessage
from tests.factories import UserFactory


class UnifiedThemeTest(TestCase):
    def test_management_and_admin_theme(self) -> None:
        user = UserFactory(is_superuser=True, is_staff=True, is_email_verified=True)
        contact = ContactMessage.objects.create(
            user=user, inquiry_type="bug", subject="UIテスト", message="テスト"
        )
        self.client.force_login(user)
        for name in ["manage_dashboard", "manage_contacts", "manage_users", "manage_analytics"]:
            with self.subTest(name=name):
                self.assertContains(self.client.get(reverse(name)), static("app/ui-components.css"))
        self.assertContains(
            self.client.get(reverse("manage_contact_update", args=[contact.pk])),
            static("app/ui-components.css"),
        )
        for path in [reverse("secure_admin:index"), reverse("secure_admin:auth_app_customuser_changelist")]:
            with self.subTest(path=path):
                self.assertContains(self.client.get(path), static("app/admin-ui.css"))
