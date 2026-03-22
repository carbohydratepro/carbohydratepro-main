#!/bin/bash
# 開発環境再起動スクリプト
# 使い方: bash restart-dev.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/3] コンテナを再起動中..."
docker-compose -f docker-compose-dev.yml down
docker-compose -f docker-compose-dev.yml up -d

echo "[2/3] コンテナ起動を待機中..."
sleep 4

echo "[3/3] 静的ファイルを収集中..."
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py collectstatic --noinput

echo "完了: 開発環境を再起動しました"
