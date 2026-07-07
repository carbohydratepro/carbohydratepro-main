"""
ミドルウェアのテスト
"""
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.http import Http404, HttpRequest, HttpResponse
from django.urls import path

from project.middleware import AdminSecurityMiddleware, MaintenanceModeMiddleware

User = get_user_model()


def _dummy_view(request: HttpRequest) -> HttpResponse:
    return HttpResponse("OK")


# AdminSecurityMiddleware のブロック検証用URLconf（本体には admin を含む名前のURLがないため）
urlpatterns = [
    path('fake-admin/', _dummy_view, name='fake_admin_page'),
]


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


class AdminSecurityMiddlewareTest(TestCase):
    """AdminSecurityMiddleware のテスト"""

    def setUp(self) -> None:
        self.factory = RequestFactory()
        self.get_response = lambda req: HttpResponse("OK", status=200)
        self.middleware = AdminSecurityMiddleware(self.get_response)

    @override_settings(ADMIN_ENABLED=False)
    def test_unnamed_url_pattern_does_not_crash(self) -> None:
        """url_name が None の名前なしURLパターンでも500にならない（本番障害の回帰テスト）"""
        # /admin/ は名前なしパターンのため resolve 結果の url_name が None になる
        request = self.factory.get('/admin/')
        request.user = type('AnonymousUser', (), {'is_authenticated': False})()
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(ADMIN_ENABLED=False)
    def test_unresolvable_path_passes_through(self) -> None:
        """resolve できないパスは通常処理を続行する"""
        request = self.factory.get('/no-such-path-xyz/')
        request.user = type('AnonymousUser', (), {'is_authenticated': False})()
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(ADMIN_ENABLED=False, ROOT_URLCONF='project.tests.test_middleware')
    def test_blocks_admin_named_url(self) -> None:
        """url_name に admin を含むURLは404でブロックされる"""
        request = self.factory.get('/fake-admin/')
        request.user = type('AnonymousUser', (), {'is_authenticated': False})()
        with self.assertRaises(Http404):
            self.middleware(request)

    @override_settings(ADMIN_ENABLED=False)
    def test_secure_admin_is_not_blocked(self) -> None:
        """secure_admin 名前空間（/system-control-panel/）はブロックされない"""
        request = self.factory.get('/system-control-panel/')
        request.user = type('AnonymousUser', (), {'is_authenticated': False})()
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(ADMIN_ENABLED=True)
    def test_no_blocking_when_admin_enabled(self) -> None:
        """ADMIN_ENABLED=True のときはブロックしない"""
        request = self.factory.get('/system-control-panel/')
        request.user = type('AnonymousUser', (), {'is_authenticated': False})()
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)


class LegacyAdminUrlTest(TestCase):
    """旧 /admin/ URL のテスト"""

    def test_legacy_admin_url_returns_404(self) -> None:
        """/admin/ は500ではなく404を返す（Http404 を raise しない旧実装の回帰テスト）"""
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 404)
