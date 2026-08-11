"""ログ監視管理コマンドのテスト。"""

from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import SimpleTestCase, override_settings
from django.utils import timezone


class DailySecurityReportCommandTest(SimpleTestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.base_dir = Path(self.temporary_directory.name)

    def _write_log(self, filename: str, lines: list[str]) -> None:
        (self.base_dir / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")

    @override_settings(SEND_PERIODIC_SECURITY_EMAIL=False)
    @patch("auth_app.management.commands.check_security_log.send_mail")
    def test_disabled_report_does_not_send_mail(self, send_mail_mock: MagicMock) -> None:
        with override_settings(BASE_DIR=self.base_dir):
            call_command("check_security_log")
        send_mail_mock.assert_not_called()

    @override_settings(
        SEND_PERIODIC_SECURITY_EMAIL=True,
        SECURITY_REPORT_MAX_DETAILS=2,
        SECURITY_ALERT_EMAIL="security@example.com",
    )
    @patch("auth_app.management.commands.check_security_log.send_mail")
    def test_report_aggregates_noise_and_limits_actionable_details(
        self,
        send_mail_mock: MagicMock,
    ) -> None:
        timestamp = timezone.localtime().strftime("%Y-%m-%d %H:%M:%S")
        self._write_log(
            "security.log",
            [
                f"WARNING {timestamp},000 middleware 1 1 Unauthenticated admin access attempt",
                f"WARNING {timestamp},000 services 1 1 存在しないユーザーへのログイン試行",
                f"WARNING {timestamp},000 services 1 1 特権ユーザーログイン検知 A",
                f"WARNING {timestamp},000 services 1 1 特権ユーザーログイン検知 B",
            ],
        )
        self._write_log(
            "django_debug.log",
            [
                f"WARNING {timestamp},000 log 1 1 Not Found: /wp-login.php",
                f"ERROR {timestamp},000 views 1 1 application error",
            ],
        )

        with override_settings(BASE_DIR=self.base_dir):
            call_command("check_security_log", hours=24)

        send_mail_mock.assert_called_once()
        call_kwargs = send_mail_mock.call_args.kwargs
        self.assertEqual(call_kwargs["recipient_list"], ["security@example.com"])
        self.assertIn("管理画面への未認証アクセス: 1件", call_kwargs["message"])
        self.assertIn("存在しないユーザーへのログイン試行: 1件", call_kwargs["message"])
        self.assertIn("- ERROR: 1件", call_kwargs["message"])
        self.assertNotIn("Not Found: /wp-login.php", call_kwargs["message"])
        self.assertEqual(call_kwargs["message"].count("特権ユーザーログイン検知"), 1)
        self.assertIn("application error", call_kwargs["message"])

    @override_settings(SEND_PERIODIC_SECURITY_EMAIL=True)
    @patch("auth_app.management.commands.check_security_log.send_mail")
    def test_report_ignores_logs_outside_window(self, send_mail_mock: MagicMock) -> None:
        timestamp = (timezone.localtime() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
        self._write_log(
            "security.log",
            [f"WARNING {timestamp},000 middleware 1 1 Unauthenticated admin access attempt"],
        )

        with override_settings(BASE_DIR=self.base_dir):
            call_command("check_security_log", hours=24)

        send_mail_mock.assert_not_called()
