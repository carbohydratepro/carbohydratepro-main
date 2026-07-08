"""
アプリシェル（トップバー・サイドバー・ボトムタブ）とスケルトンのテスト
"""
from django.test import Client, TestCase

from tests.factories import UserFactory


class AppShellTest(TestCase):
    """ログイン済みページのシェル構造のテスト"""

    def setUp(self) -> None:
        self.client = Client()
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_dashboard_has_shell(self) -> None:
        """ダッシュボードにトップバー・サイドバー・ボトムタブが描画されること"""
        response = self.client.get('/carbohydratepro/home/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'app-topbar')
        self.assertContains(response, 'app-sidebar')
        self.assertContains(response, 'app-bottomnav')
        self.assertContains(response, 'has-bottomnav')

    def test_sidebar_marks_active_link(self) -> None:
        """サイドバーの現在ページリンクに active が付くこと"""
        response = self.client.get('/carbohydratepro/home/')
        content = response.content.decode('utf-8')
        self.assertIn('side-link active', content)

    def test_authenticated_registration_page_uses_shell(self) -> None:
        """ログイン済みのアカウント編集画面も同じシェルを使うこと"""
        response = self.client.get('/accounts/edit/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'app-sidebar')
        self.assertContains(response, 'app-bottomnav')


class AnonymousLayoutTest(TestCase):
    """未ログインページのレイアウトのテスト"""

    def setUp(self) -> None:
        self.client = Client()

    def test_login_page_keeps_top_navbar(self) -> None:
        """ログインページは従来のトップナビでサイドバーを出さないこと"""
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'navbar')
        self.assertNotContains(response, 'app-sidebar')
        self.assertNotContains(response, 'app-bottomnav')


class DemoShellTest(TestCase):
    """デモモードのシェルのテスト"""

    def test_demo_home_has_shell_with_demo_links(self) -> None:
        """デモホームにシェルとデモ用リンクが描画されること"""
        response = Client().get('/demo/home/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'app-sidebar')
        self.assertContains(response, 'app-bottomnav')
        self.assertContains(response, '/demo/expenses/')
