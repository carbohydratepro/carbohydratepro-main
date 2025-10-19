#!/bin/bash
# このスクリプトは非推奨です
# 代わりに以下の2つのスクリプトを使用してください：
# - check_security_only.sh (1分ごとに実行)
# - check_debug_only.sh (5分ごとに実行)

echo "警告: このスクリプトは非推奨です。"
echo "check_security_only.sh と check_debug_only.sh を使用してください。"
echo ""

cd /home/carbohydratepro-main

# セキュリティログチェック
python manage.py check_security_log >> security_check.log 2>&1

# デバッグログチェック
python manage.py check_debug_log >> debug_check.log 2>&1
