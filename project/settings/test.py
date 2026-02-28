"""テスト環境用設定。

使い方:
    python manage.py test --settings=project.settings.test
"""

from .base import *  # noqa: F401, F403

DEBUG = True

SITE_DOMAIN = 'testserver'
SITE_PROTOCOL = 'http'

# Django 4.0+ の CSRF 検証で必要（Origin ヘッダーの許可リスト）
CSRF_TRUSTED_ORIGINS = ['http://testserver']

ADMIN_ENABLED = True

# テスト用メールバックエンド（実際にメールを送信しない）
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# パスワードハッシュを軽量化してテストを高速化
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
