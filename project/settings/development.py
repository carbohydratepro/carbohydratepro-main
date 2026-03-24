"""開発環境用設定。"""

from .base import *  # noqa: F401, F403

DEBUG = True

SITE_DOMAIN = env('SITE_DOMAIN', default='localhost:8000')  # noqa: F405
SITE_PROTOCOL = 'http'

# Django 4.0+ の CSRF 検証で必要（Origin ヘッダーの許可リスト）
CSRF_TRUSTED_ORIGINS = [
    f'{SITE_PROTOCOL}://{SITE_DOMAIN}',
    'http://127.0.0.1:8000',
]

# 開発環境では管理サイトを有効化
ADMIN_ENABLED = env.bool('ADMIN_ENABLED', default=True)  # noqa: F405
