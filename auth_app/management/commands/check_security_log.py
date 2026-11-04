"""セキュリティイベントと重大エラーを日次集約して通知する。"""

from datetime import date, datetime, timedelta
from typing import Any

from django.conf import settings
from django.core.mail import get_connection, send_mail
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from auth_app.models import SecurityReportDelivery


class Command(BaseCommand):
    help = "セキュリティイベントとERROR/CRITICALを指定期間で集約して1通通知する"

    CLAIM_TIMEOUT = timedelta(minutes=30)

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--urgent', action='store_true', help='重要イベントだけを集約して通知する')
        parser.add_argument(
            "--hours",
            type=float,
            default=24.0,
            help="集計対象とする直近時間（既定: 24時間）",
        )

    def handle(self, *args: object, **options: Any) -> None:
        from collections import Counter
        from auth_app.security_collection import collect_events
        from auth_app.security_models import SecurityEvent
        from auth_app.security_notifications import send_urgent_report
        from auth_app.security_rules import LABELS

        hours = float(options['hours'])
        if hours <= 0 or hours > 168:
            raise CommandError('--hours は0より大きく168以下にしてください')
        now = timezone.now()
        try:
            collect_events(now)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            if options['urgent']:
                send_urgent_report(now)
            raise CommandError('ログ取り込みに失敗しました。監視元を確認してください') from exc
        if options['urgent']:
            sent = send_urgent_report(now)
            self.stdout.write('重要イベントを1通通知しました' if sent else '新しい速報対象はありません')
            return
        if not settings.SEND_PERIODIC_SECURITY_EMAIL:
            self.stdout.write('定期セキュリティレポートは無効です（集計は継続）')
            return
        start = now - timedelta(hours=hours)
        events = SecurityEvent.objects.filter(occurred_at__gte=start, occurred_at__lte=now)
        counts = Counter(events.values_list('category', flat=True))
        if not counts:
            self.stdout.write('集計対象はありません')
            return
        report_date = timezone.localdate(now)
        if not self._claim_delivery(report_date, now):
            self.stdout.write('本日の日次レポートは送信済みまたは送信中です')
            return
        security_count = events.filter(source='security').count()
        error_count = events.filter(severity='error').count()
        critical_count = events.filter(severity='critical').count()
        lines = ['日次セキュリティ・エラーレポート',
            f'監視期間: {timezone.localtime(start):%Y-%m-%d %H:%M:%S} ～ {timezone.localtime(now):%Y-%m-%d %H:%M:%S}', '',
            f'検出総数: {events.count()}件',
            f'- CRITICAL: {critical_count}件', f'- ERROR: {error_count}件', '']
        lines += [f'- {LABELS.get(category, category)}: {count}件' for category, count in sorted(counts.items())]
        lines += ['', '拒否済みアクセスや予定メンテナンスは侵入・障害の確定情報ではありません。',
                  'ログ本文・認証情報はメールへ転記していません。詳細は管理パネルで確認してください。']
        try:
            delivered = send_mail(subject=f'【日次セキュリティレポート】検出{events.count()}件',
                message='\n'.join(lines), from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.SECURITY_ALERT_EMAIL], fail_silently=False, connection=get_connection(timeout=15))
            if delivered == 0:
                raise RuntimeError('Mail backend did not accept the report')
        except Exception as exc:
            SecurityReportDelivery.objects.filter(report_date=report_date, attempted_at=now).update(status='failed')
            raise CommandError('日次セキュリティレポート送信エラー') from exc
        SecurityReportDelivery.objects.filter(report_date=report_date, attempted_at=now).update(
            status='sent', sent_at=timezone.now(), security_event_count=security_count,
            critical_error_count=critical_count+error_count)
        self.stdout.write('日次セキュリティレポートを1通送信しました')

    def _claim_delivery(self, report_date: date, attempted_at: datetime) -> bool:
        """同日の送信権をDB行ロックで1実行だけに与える。"""
        stale_before = attempted_at - self.CLAIM_TIMEOUT
        with transaction.atomic():
            delivery, created = (
                SecurityReportDelivery.objects.select_for_update().get_or_create(
                    report_date=report_date,
                    defaults={
                        "status": SecurityReportDelivery.STATUS_SENDING,
                        "attempted_at": attempted_at,
                    },
                )
            )
            if created:
                return True
            if delivery.status == SecurityReportDelivery.STATUS_SENT:
                return False
            if (
                delivery.status == SecurityReportDelivery.STATUS_SENDING
                and delivery.attempted_at > stale_before
            ):
                return False

            delivery.status = SecurityReportDelivery.STATUS_SENDING
            delivery.attempted_at = attempted_at
            delivery.sent_at = None
            delivery.save(update_fields=["status", "attempted_at", "sent_at"])
            return True
