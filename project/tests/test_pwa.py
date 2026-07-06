"""
PWA関連エンドポイントのテスト
"""
from django.contrib.staticfiles import finders
from django.test import Client, TestCase


class PwaEndpointsTest(TestCase):
    """Service Worker・オフラインページ・マニフェストのテスト"""

    def setUp(self) -> None:
        self.client = Client()

    def test_service_worker_served_at_root(self) -> None:
        """/sw.js がルートスコープでJavaScriptとして配信されること"""
        response = self.client.get('/sw.js')
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/javascript', response['Content-Type'])
        content = response.content.decode('utf-8')
        self.assertIn('addEventListener', content)
        self.assertIn('/offline/', content)

    def test_offline_page(self) -> None:
        """オフラインページが自己完結で表示できること"""
        response = self.client.get('/offline/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'オフライン')
        # CDN非依存（オフラインで表示するため外部リソースを参照しない）
        self.assertNotContains(response, 'https://stackpath.bootstrapcdn.com')
        self.assertNotContains(response, 'https://cdnjs.cloudflare.com')

    def test_manifest_exists_in_static(self) -> None:
        """Webアプリマニフェストが静的ファイルとして存在すること"""
        path = finders.find('app/manifest.webmanifest')
        self.assertIsNotNone(path)

    def test_login_page_links_manifest(self) -> None:
        """ログインページにmanifestリンクとSW登録スクリプトがあること"""
        response = self.client.get('/login/')
        # 静的ファイル名はコンテンツハッシュ付きになるため拡張子・接頭辞で確認する
        self.assertContains(response, 'rel="manifest"')
        self.assertContains(response, '.webmanifest')
        self.assertContains(response, '/static/app/pwa.')
