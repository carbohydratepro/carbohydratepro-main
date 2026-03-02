"""本番環境用設定。"""

from .base import *  # noqa: F401, F403

DEBUG = False

SITE_DOMAIN = env('SITE_DOMAIN', default='carbohydratepro.com')  # noqa: F405
SITE_PROTOCOL = 'https'

# Django 4.0+ の CSRF 検証で必要（Origin ヘッダーの許可リスト）
CSRF_TRUSTED_ORIGINS = [f'{SITE_PROTOCOL}://{SITE_DOMAIN}']

# CloudFront / ロードバランサー経由の HTTPS を Django に伝える
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# 本番環境では管理サイトをデフォルト無効化
ADMIN_ENABLED = env.bool('ADMIN_ENABLED', default=False)  # noqa: F405

# セキュリティヘッダー（本番環境用）
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
