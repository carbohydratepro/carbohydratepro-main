#!/bin/bash
# デバッグログ監視スクリプト（5分ごとに実行）

cd /home/carbohydratepro-main

echo "[$(date '+%Y-%m-%d %H:%M:%S')] デバッグログチェック開始" >> debug_check.log
python manage.py check_debug_log >> debug_check.log 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] デバッグログチェック完了" >> debug_check.log
echo "" >> debug_check.log
