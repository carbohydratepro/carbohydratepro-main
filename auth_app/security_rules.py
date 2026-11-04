"""記録の分類。未検証のログ本文を通知・管理画面へ転記しない。"""
import re
from datetime import datetime
from django.utils import timezone

LABELS = {
    'app_error': 'アプリケーションエラー',
    'app_critical': 'アプリケーションの重大ログ',
    'app_error_burst': '5分間に10件以上のアプリケーションエラー',
    'maintenance': '予定されたメンテナンス応答',
    'admin_probe': '管理画面の探索',
    'csrf': 'CSRF・Referer検証による拒否',
    'denied': 'アクセス拒否',
    'login_failure': 'ログイン失敗・ロック',
    'privileged_login': '特権ユーザーのログイン（本人確認が必要）',
    'other': 'その他のセキュリティ記録',
    'ssh_login': '許可範囲からのSSHログイン',
    'ssh_unexpected_login': '許可範囲外からのSSHログイン',
    'ssh_failure': 'SSH認証失敗',
    'ssh_burst': 'SSH認証失敗の集中',
    'file_integrity': '監視対象ファイルの追加・変更・削除',
    'suspicious_file': 'アップロード領域の実行形式ファイル',
    'new_listener': '新しい待受ポート',
    'host_monitor_failure': 'サーバー監視処理の異常',
    'host_monitor_stale': 'サーバー監視の更新停止',
}
HOST_CRITICAL = {'ssh_unexpected_login', 'ssh_burst', 'file_integrity', 'suspicious_file',
                 'new_listener', 'host_monitor_failure'}
HOST_CATEGORIES = HOST_CRITICAL | {'ssh_login', 'ssh_failure'}
HEADER = re.compile(r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL) (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)(?:,(\d{3}))?\s')


def parse_application_line(line: str, source: str) -> tuple[datetime, str, str] | None:
    match = HEADER.match(line)
    if not match:
        return None
    level, stamp, millis = match.groups()
    try:
        occurred = timezone.make_aware(datetime.strptime(stamp, '%Y-%m-%d %H:%M:%S').replace(
            microsecond=int(millis or 0) * 1000), timezone.get_default_timezone())
    except ValueError:
        return None
    message = re.sub(r'^\S+ \d+ \d+ ', '', line[match.end():].strip())
    if level == 'INFO' and message == 'Planned maintenance response':
        return occurred, 'maintenance', 'info'
    # 拒否・探索のログは、書き手がCRITICALとした場合でも侵入成功とは扱わない。
    lower = message.lower()
    if source == 'security' and re.match(r'^(?:blocked admin access attempt|unauthenticated admin access attempt|suspicious access attempt)(?:\s|$)', lower):
        return occurred, 'admin_probe', 'warning'
    if level == 'WARNING' and ('csrf' in lower or 'referer checking failed' in lower):
        return occurred, 'csrf', 'warning'
    if level == 'WARNING' and lower.startswith('forbidden'):
        return occurred, 'denied', 'warning'
    if level == 'WARNING' and '特権ユーザーログイン検知' in message:
        return occurred, 'privileged_login', 'warning'
    if level == 'WARNING' and 'ログイン試行' in message:
        return occurred, 'login_failure', 'warning'
    if level == 'CRITICAL':
        return occurred, 'app_critical', 'critical'
    if level == 'ERROR':
        return occurred, 'app_error', 'error'
    if source == 'security' and level == 'WARNING':
        return occurred, 'other', 'warning'
    return None
