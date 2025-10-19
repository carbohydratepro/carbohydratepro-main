@echo off
REM このスクリプトは非推奨です
REM 代わりに以下の2つのスクリプトを使用してください：
REM - check_security_only.bat (1分ごとに実行)
REM - check_debug_only.bat (5分ごとに実行)

echo 警告: このスクリプトは非推奨です。
echo check_security_only.bat と check_debug_only.bat を使用してください。
echo.

cd /d "\\wsl.localhost\archlinux\home\carbohydratepro-main"

REM セキュリティログチェック
python manage.py check_security_log >> security_check.log 2>&1

REM デバッグログチェック
python manage.py check_debug_log >> debug_check.log 2>&1
