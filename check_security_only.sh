#!/bin/bash
# セキュリティログ監視スクリプト（1分ごとに実行）

cd /home/carbohydratepro-main

echo "[$(date '+%Y-%m-%d %H:%M:%S')] セキュリティログチェック開始" >> security_check.log
python manage.py check_security_log >> security_check.log 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] セキュリティログチェック完了" >> security_check.log
echo "" >> security_check.log
