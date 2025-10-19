"""
django_debug.logを監視し、過去5分間にエラーログがあればメール通知を送信する管理コマンド
使用方法: python manage.py check_debug_log
"""

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
import os
import re


class Command(BaseCommand):
    help = 'django_debug.logを監視し、過去5分間にエラーログがあればメール通知を送信'

    def handle(self, *args, **options):
        # django_debug.logファイルのパス
        log_file_path = os.path.join(settings.BASE_DIR, 'django_debug.log')
        
        if not os.path.exists(log_file_path):
            self.stdout.write(self.style.WARNING('django_debug.logファイルが見つかりません'))
            return
        
        # 現在時刻と5分前の時刻を取得
        now = datetime.now()
        five_minutes_ago = now - timedelta(minutes=5)
        
        # デバッグログから過去5分間のエラーエントリを抽出
        recent_errors = []
        recent_warnings = []
        recent_criticals = []
        recent_tracebacks = []
        
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                in_traceback = False
                current_traceback = []
                traceback_time = None
                
                for line in f:
                    # 空行はスキップ（ただしTraceback内は保持）
                    if not line.strip() and not in_traceback:
                        continue
                    
                    # Tracebackの開始を検知
                    if 'Traceback (most recent call last)' in line:
                        in_traceback = True
                        current_traceback = [line.strip()]
                        # 前の行のタイムスタンプを使用する（Traceback自体にはタイムスタンプがないため）
                        traceback_time = None
                        continue
                    
                    # Traceback内の処理
                    if in_traceback:
                        current_traceback.append(line.rstrip())
                        # Tracebackの終了を検知（例外メッセージで終わる）
                        # 通常、インデントされていない行でTracebackが終わる
                        if line and not line.startswith(' ') and not line.startswith('\t') and 'Error:' in line or 'Exception:' in line:
                            # Tracebackを保存
                            if traceback_time and traceback_time >= five_minutes_ago and traceback_time <= now:
                                recent_tracebacks.append('\n'.join(current_traceback))
                            in_traceback = False
                            current_traceback = []
                            traceback_time = None
                        continue
                    
                    # ログのタイムスタンプを抽出（例: 2025-10-20 15:30:45,123）
                    # Djangoのログ形式: LEVEL YYYY-MM-DD HH:MM:SS,mmm ...
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    
                    if timestamp_match:
                        try:
                            log_time_str = timestamp_match.group(1)
                            log_time = datetime.strptime(log_time_str, '%Y-%m-%d %H:%M:%S')
                            
                            # Tracebackのタイムスタンプとして記録
                            traceback_time = log_time
                            
                            # 過去5分間のログのみを対象
                            if log_time >= five_minutes_ago and log_time <= now:
                                # エラーレベルで分類
                                if line.startswith('CRITICAL'):
                                    recent_criticals.append(line.strip())
                                elif line.startswith('ERROR'):
                                    recent_errors.append(line.strip())
                                elif line.startswith('WARNING'):
                                    recent_warnings.append(line.strip())
                        except ValueError:
                            # タイムスタンプのパースに失敗した場合はスキップ
                            continue
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'ログファイル読み込みエラー: {str(e)}'))
            return
        
        # エラー、警告、クリティカル、Tracebackのログがあればメール送信
        total_logs = len(recent_criticals) + len(recent_errors) + len(recent_warnings) + len(recent_tracebacks)
        
        if total_logs > 0:
            self.send_debug_log_alert(
                recent_criticals, 
                recent_errors, 
                recent_warnings,
                recent_tracebacks,
                five_minutes_ago, 
                now
            )
            self.stdout.write(self.style.SUCCESS(
                f'デバッグログアラートメールを送信しました（{total_logs}件のログ）'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('過去5分間に新しいエラーログはありません'))
    
    def send_debug_log_alert(self, criticals, errors, warnings, tracebacks, start_time, end_time):
        """デバッグログアラートメールを送信"""
        
        total_logs = len(criticals) + len(errors) + len(warnings) + len(tracebacks)
        subject = f'【Djangoエラーレポート】アプリケーションエラー検知 ({total_logs}件)'
        
        # メール本文を作成
        message = f'''
Djangoアプリケーション エラーレポート

【監視期間】
{start_time.strftime('%Y-%m-%d %H:%M:%S')} ～ {end_time.strftime('%Y-%m-%d %H:%M:%S')}

【検知件数サマリー】
総エラー数: {total_logs}件
- CRITICAL: {len(criticals)}件
- ERROR: {len(errors)}件
- WARNING: {len(warnings)}件
- Traceback: {len(tracebacks)}件

'''
        
        # CRITICAL ログ
        if criticals:
            message += '=' * 60 + '\n'
            message += '【CRITICAL - 重大なエラー】\n'
            message += '=' * 60 + '\n'
            for i, log in enumerate(criticals, 1):
                message += f'\n{i}. {log}\n'
            message += '\n'
        
        # ERROR ログ
        if errors:
            message += '=' * 60 + '\n'
            message += '【ERROR - エラー】\n'
            message += '=' * 60 + '\n'
            for i, log in enumerate(errors, 1):
                message += f'\n{i}. {log}\n'
            message += '\n'
        
        # WARNING ログ
        if warnings:
            message += '=' * 60 + '\n'
            message += '【WARNING - 警告】\n'
            message += '=' * 60 + '\n'
            for i, log in enumerate(warnings, 1):
                message += f'\n{i}. {log}\n'
            message += '\n'
        
        # Traceback ログ
        if tracebacks:
            message += '=' * 60 + '\n'
            message += '【Traceback - スタックトレース】\n'
            message += '=' * 60 + '\n'
            for i, traceback in enumerate(tracebacks, 1):
                message += f'\n--- Traceback #{i} ---\n{traceback}\n'
            message += '\n'
        
        message += '''
============================================================
対応が必要なエラーについては、速やかに確認してください。
継続的なエラーが発生している場合は、アプリケーションの動作に
問題が発生している可能性があります。

---
このメールは5分ごとに自動送信されています。
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
