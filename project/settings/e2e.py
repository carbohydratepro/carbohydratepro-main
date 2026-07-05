"""E2E テスト用設定。"""

from .development import *  # noqa: F401, F403

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
SEND_INSTANT_SECURITY_EMAIL = False
SEND_PERIODIC_SECURITY_EMAIL = False

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
