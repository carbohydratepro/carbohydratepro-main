"""外部カレンダー（ICS購読）の定期同期コマンド。cronから30分ごとに実行される。"""
import logging

from django.core.management.base import BaseCommand

from app.task import services
from app.task.models import ExternalCalendar

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '登録済みの外部カレンダーを同期する'

    def handle(self, *args: object, **options: object) -> None:
        calendars = ExternalCalendar.objects.all()
        success_count = 0
        failure_count = 0
        for external_calendar in calendars:
            success, message = services.sync_external_calendar_safe(external_calendar)
            if success:
                success_count += 1
            else:
                failure_count += 1
                logger.warning(
                    '外部カレンダー同期失敗 | id=%s user=%s name=%s | %s',
                    external_calendar.id,
                    external_calendar.user_id,
                    external_calendar.name,
                    message,
                )
        self.stdout.write(
            f'外部カレンダー同期完了: 成功 {success_count}件 / 失敗 {failure_count}件'
        )
