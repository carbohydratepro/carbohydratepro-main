"""サイトマップ定義"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class PublicPagesSitemap(Sitemap):
    """公開ページのサイトマップ"""
    protocol = 'https'
    changefreq = 'weekly'
    priority = 0.8

    def items(self) -> list[str]:
        return [
            'top',
            'login',
            'signup',
            'demo_expenses',
            'demo_tasks',
            'demo_habits',
            'demo_memos',
            'demo_shopping',
            'demo_board',
        ]

    def location(self, item: str) -> str:
        return reverse(item)

    def priority(self, item: str) -> float:  # type: ignore[override]
        if item == 'top':
            return 1.0
        if item.startswith('demo_'):
            return 0.7
        return 0.5
