"""
セキュリティログを監視し、過去1分間に記録があればメール通知を送信する管理コマンド
使用方法: python manage.py check_security_log
"""

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
import os
import re


class Command(BaseCommand):
    help = 'セキュリティログを監視し、過去1分間に新しいログがあればメール通知を送信'

    def handle(self, *args, **options):
        # セキュリティログファイルのパス
        log_file_path = os.path.join(settings.BASE_DIR, 'security.log')
        
        if not os.path.exists(log_file_path):
            self.stdout.write(self.style.WARNING('security.logファイルが見つかりません'))
            return
        
        # 現在時刻と1分前の時刻を取得
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        # セキュリティログから過去1分間のエントリを抽出
        recent_logs = []
        
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # 空行はスキップ
                    if not line.strip():
                        continue
                    
                    # ログのタイムスタンプを抽出（例: 2025-10-20 15:30:45）
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    
                    if timestamp_match:
                        try:
                            log_time_str = timestamp_match.group(1)
                            log_time = datetime.strptime(log_time_str, '%Y-%m-%d %H:%M:%S')
                            
                            # 過去1分間のログのみを対象（すべてのセキュリティイベント）
                            if log_time >= one_minute_ago and log_time <= now:
                                recent_logs.append(line.strip())
                        except ValueError:
                            # タイムスタンプのパースに失敗した場合はスキップ
                            continue
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'ログファイル読み込みエラー: {str(e)}'))
            return
        
        # 過去1分間にログがあればメール送信
        if recent_logs:
            self.send_security_alert(recent_logs, one_minute_ago, now)
            self.stdout.write(self.style.SUCCESS(
                f'セキュリティアラートメールを送信しました（{len(recent_logs)}件のログ）'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('過去1分間に新しいセキュリティログはありません'))
    
    def send_security_alert(self, logs, start_time, end_time):
        """セキュリティアラートメールを送信"""
        
        # ログの種類を分類
        login_logs = [log for log in logs if '特権ユーザーログイン検知' in log]
        warning_logs = [log for log in logs if 'WARNING' in log and log not in login_logs]
        error_logs = [log for log in logs if 'ERROR' in log]
        other_logs = [log for log in logs if log not in login_logs and log not in warning_logs and log not in error_logs]
        
        subject = f'【定期セキュリティレポート】セキュリティイベント検知 ({len(logs)}件)'
        
        # メール本文を作成
        message = f'''
定期セキュリティレポート

【監視期間】
{start_time.strftime('%Y-%m-%d %H:%M:%S')} ～ {end_time.strftime('%Y-%m-%d %H:%M:%S')}

【検知件数サマリー】
総イベント数: {len(logs)}件
- 特権ユーザーログイン: {len(login_logs)}件
- 警告 (WARNING): {len(warning_logs)}件
- エラー (ERROR): {len(error_logs)}件
- その他: {len(other_logs)}件

'''
        
        # 特権ユーザーログイン
        if login_logs:
            message += '【特権ユーザーログイン】\n'
            for i, log in enumerate(login_logs, 1):
                message += f'{i}. {log}\n'
            message += '\n'
        
        # 警告ログ
        if warning_logs:
            message += '【警告ログ】\n'
            for i, log in enumerate(warning_logs, 1):
                message += f'{i}. {log}\n'
            message += '\n'
        
        # エラーログ
        if error_logs:
            message += '【エラーログ】\n'
            for i, log in enumerate(error_logs, 1):
                message += f'{i}. {log}\n'
            message += '\n'
        
        # その他のログ
        if other_logs:
            message += '【その他のセキュリティイベント】\n'
            for i, log in enumerate(other_logs, 1):
                message += f'{i}. {log}\n'
            message += '\n'
        
        message += '''---
このメールは1分ごとに自動送信されています。
不審なアクティビティを検知した場合は、直ちに管理者に連絡してください。
'''
        
        try:
            recipient_email = getattr(settings, 'SECURITY_ALERT_EMAIL', 'carbohydratepro@gmail.com')
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'メール送信エラー: {str(e)}'))
