"""セキュリティイベントと重大エラーを日次集約して通知する。"""

from datetime import timedelta
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils import timezone

from auth_app.log_monitoring import (
    actionable_details,
    classify_security_logs,
    log_paths,
    recent_log_lines,
)


CATEGORY_LABELS: tuple[tuple[str, str], ...] = (
    ("privileged_login", "特権ユーザーログイン"),
    ("unknown_login", "存在しないユーザーへのログイン試行"),
    ("locked_login", "ロック中アカウントへのログイン試行"),
    ("admin_probe", "管理画面への未認証アクセス"),
    ("csrf", "CSRF拒否"),
    ("forbidden", "その他のアクセス拒否"),
    ("other", "その他"),
)


class Command(BaseCommand):
    help = "セキュリティイベントとERROR/CRITICALを指定期間で集約して1通通知する"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--hours",
            type=float,
            default=24.0,
            help="集計対象とする直近時間（既定: 24時間）",
        )

    def handle(self, *args: object, **options: Any) -> None:
        if not getattr(settings, "SEND_PERIODIC_SECURITY_EMAIL", True):
            self.stdout.write("定期セキュリティレポートは無効です")
            return

        hours = float(options["hours"])
        if hours <= 0:
            raise CommandError("--hours には0より大きい値を指定してください")

        end = timezone.localtime().replace(tzinfo=None)
        start = end - timedelta(hours=hours)
        base_dir = Path(settings.BASE_DIR)
        security_lines = recent_log_lines(
            log_paths(base_dir, "security.log"),
            start,
            end,
        )
        debug_lines = recent_log_lines(
            log_paths(base_dir, "django_debug.log"),
            start,
            end,
        )
        critical_count = sum(line.startswith("CRITICAL") for line in debug_lines)
        error_count = sum(line.startswith("ERROR") for line in debug_lines)

        if not security_lines and critical_count == 0 and error_count == 0:
            self.stdout.write("集計対象のセキュリティイベント・重大エラーはありません")
            return

        counts = classify_security_logs(security_lines)
        max_details = int(getattr(settings, "SECURITY_REPORT_MAX_DETAILS", 20))
        details = actionable_details(security_lines, debug_lines)[:max_details]
        summary_lines = [
            "日次セキュリティ・エラーレポート",
            "",
            f"監視期間: {start:%Y-%m-%d %H:%M:%S} ～ {end:%Y-%m-%d %H:%M:%S}",
            "",
            "【セキュリティイベント】",
            f"総件数: {len(security_lines)}件",
        ]
        summary_lines.extend(
            f"- {label}: {counts.get(category, 0)}件"
            for category, label in CATEGORY_LABELS
        )
        summary_lines.extend(
            [
                "",
                "【アプリケーション重大ログ】",
                f"- CRITICAL: {critical_count}件",
                f"- ERROR: {error_count}件",
            ]
        )
        if details:
            summary_lines.extend(["", f"【要確認の詳細（最大{max_details}件）】"])
            summary_lines.extend(
                f"{index}. {line[:2000]}" for index, line in enumerate(details, 1)
            )
        summary_lines.extend(
            [
                "",
                "管理画面探索やCSRF拒否などの日常的なインターネットノイズは件数のみ集約しています。",
            ]
        )

        recipient = getattr(settings, "SECURITY_ALERT_EMAIL", "carbohydratepro@gmail.com")
        try:
            send_mail(
                subject=(
                    "【日次セキュリティレポート】"
                    f"イベント{len(security_lines)}件・重大ログ{critical_count + error_count}件"
                ),
                message="\n".join(summary_lines),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
        except Exception as exc:
            raise CommandError(f"日次セキュリティレポート送信エラー: {exc}") from exc

        self.stdout.write(
            self.style.SUCCESS(
                "日次セキュリティレポートを1通送信しました "
                f"（セキュリティ{len(security_lines)}件、重大ログ{critical_count + error_count}件）"
            )
        )
