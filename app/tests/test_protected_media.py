import tempfile

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import Client, TestCase, override_settings

from app.cooking.models import CookingDish
from tests.factories import UserFactory


class ProtectedMediaTest(TestCase):
    def setUp(self) -> None:
        self.media_directory = tempfile.TemporaryDirectory()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.media_directory.name,
            DEBUG=True,
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.addCleanup(self.media_directory.cleanup)
        self.client = Client()
        self.user = UserFactory()
        self.other_user = UserFactory()

    def _save_file(self, path: str) -> None:
        default_storage.save(path, ContentFile(b'private-image'))

    def test_cooking_photo_requires_its_owner(self) -> None:
        path = f'cooking/{self.user.pk}/dish.jpg'
        self._save_file(path)
        CookingDish.objects.create(user=self.user, title='料理', photo_1=path)

        anonymous_response = self.client.get(f'/media/{path}')
        self.client.force_login(self.other_user)
        other_response = self.client.get(f'/media/{path}')
        self.client.force_login(self.user)
        owner_response = self.client.get(f'/media/{path}')

        self.assertEqual(anonymous_response.status_code, 302)
        self.assertEqual(other_response.status_code, 404)
        self.assertEqual(owner_response.status_code, 200)
        self.assertEqual(b''.join(owner_response.streaming_content), b'private-image')
        self.assertEqual(owner_response['Cache-Control'], 'private, no-store')

    def test_avatar_requires_its_owner(self) -> None:
        path = 'account_avatars/private.png'
        self._save_file(path)
        self.user.avatar = path
        self.user.save(update_fields=['avatar'])

        self.client.force_login(self.other_user)
        self.assertEqual(self.client.get(f'/media/{path}').status_code, 404)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(f'/media/{path}').status_code, 200)

    def test_production_response_uses_internal_nginx_redirect(self) -> None:
        path = f'cooking/{self.user.pk}/dish.jpg'
        self._save_file(path)
        CookingDish.objects.create(user=self.user, title='料理', photo_1=path)
        self.client.force_login(self.user)

        with override_settings(DEBUG=False):
            response = self.client.get(f'/media/{path}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['X-Accel-Redirect'], f'/_protected_media/{path}')

    def test_unknown_media_and_traversal_are_not_served(self) -> None:
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/media/other/file.txt').status_code, 404)
        self.assertEqual(self.client.get('/media/cooking/../secret.txt').status_code, 404)
