@echo off
REM セキュリティログ監視スクリプト（1分ごとに実行）
cd /d \\wsl.localhost\archlinux\home\carbohydratepro-main

echo [%date% %time%] セキュリティログチェック開始 >> security_check.log
python manage.py check_security_log >> security_check.log 2>&1
echo [%date% %time%] セキュリティログチェック完了 >> security_check.log
echo. >> security_check.log
