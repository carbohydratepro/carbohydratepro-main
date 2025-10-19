@echo off
REM デバッグログ監視スクリプト（5分ごとに実行）
cd /d \\wsl.localhost\archlinux\home\carbohydratepro-main

echo [%date% %time%] デバッグログチェック開始 >> debug_check.log
python manage.py check_debug_log >> debug_check.log 2>&1
echo [%date% %time%] デバッグログチェック完了 >> debug_check.log
echo. >> debug_check.log
