"""予定されたメンテナンスの503だけを通常の運用記録にする。"""
import logging


class PlannedMaintenanceFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        request = getattr(record, 'request', None)
        if getattr(record, 'status_code', None) == 503 and getattr(
            request, '_planned_maintenance_response', False
        ):
            record.levelno = logging.INFO
            record.levelname = 'INFO'
            record.msg = 'Planned maintenance response'
            record.args = ()
        return True
