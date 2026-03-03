"""
ミドルウェアのテスト
"""
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse

from project.middleware import MaintenanceModeMiddleware

User = get_user_model()


class MaintenanceModeMiddlewareTest(TestCase):
    """MaintenanceModeMiddleware のテスト"""

    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.get_response = lambda req: HttpResponse("OK", status=200)
        self.middleware = MaintenanceModeMiddleware(self.get_response)

    @override_settings(MAINTENANCE_MODE=True)
    def test_returns_503_during_maintenance(self) -> None:
        """メンテナンスモード中は503を返す"""
        request = self.factory.get('/')
        request.user = type('AnonymousUser', (), {'is_authenticated': False, 'is_staff': False})()
        response = self.middleware(request)
        self.assertEqual(response.status_code, 503)

    @override_settings(MAINTENANCE_MODE=False)
    def test_passes_through_when_not_maintenance(self) -> None:
        """メンテナンスモード無効時は通常レスポンスを返す"""
        request = self.factory.get('/')
        request.user = type('AnonymousUser', (), {'is_authenticated': False, 'is_staff': False})()
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(MAINTENANCE_MODE=True)
    def test_staff_can_bypass_maintenance(self) -> None:
        """スタッフユーザーはメンテナンスをバイパスできる"""
        request = self.factory.get('/')
        staff_user = User.objects.create_user(username='staff', email='staff@example.com', password='pass', is_staff=True)
        request.user = staff_user
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(MAINTENANCE_MODE=True)
    def test_static_files_bypass_maintenance(self) -> None:
        """静的ファイルはメンテナンス中でも通過する"""
        request = self.factory.get('/static/app/styles.css')
        request.user = type('AnonymousUser', (), {'is_authenticated': False, 'is_staff': False})()
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)
