#!/bin/bash
set -euo pipefail

#=============================================================================
# 本番デプロイスクリプト
#
# 使い方:
#   ./deploy.sh [user@host] [branch]
#
# 例:
#   ./deploy.sh                              # デフォルトホスト、main ブランチをデプロイ
#   ./deploy.sh 54.238.169.177              # 指定ホスト、main ブランチをデプロイ
#   ./deploy.sh 54.238.169.177 develop      # 指定ホスト、develop ブランチをデプロイ
#
# 前提条件:
#   - SSH 鍵認証が設定済みであること
#   - リモートサーバーに Docker と Docker Compose がインストール済みであること
#   - リモートサーバーの ~/carbohydratepro にリポジトリがクローン済みであること
#   - secret.env がリモートサーバー上に配置済みであること
#=============================================================================

REMOTE_HOST="${1:-54.238.169.177}"
BRANCH="${2:-main}"
REMOTE_DIR="carbohydratepro"
COMPOSE_FILE="docker-compose.yml"

echo "============================================"
echo " デプロイ開始"
echo " ホスト: ${REMOTE_HOST}"
echo " ブランチ: ${BRANCH}"
echo "============================================"

# 1. ローカルの変更確認
echo ""
echo "[1/6] ローカルの未コミット変更を確認中..."
if [ -n "$(git status --porcelain)" ]; then
    echo "警告: 未コミットの変更があります"
    git status --short
    read -r -p "このまま続行しますか？ (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "デプロイを中止しました"
        exit 1
    fi
fi

# 2. リモートサーバーで最新コードを取得
echo ""
echo "[2/6] リモートサーバーで最新コードを取得中..."
ssh "${REMOTE_HOST}" bash -s <<EOF
    set -euo pipefail
    cd ${REMOTE_DIR}
    git fetch origin
    git checkout ${BRANCH}
    git pull origin ${BRANCH}
    echo "現在のコミット: \$(git log --oneline -1)"
EOF

# 3. コンテナのビルド
echo ""
echo "[3/6] コンテナをビルド中..."
ssh "${REMOTE_HOST}" bash -s <<EOF
    set -euo pipefail
    cd ${REMOTE_DIR}
    docker-compose -f ${COMPOSE_FILE} build
EOF

# 4. コンテナの再起動
echo ""
echo "[4/6] コンテナを再起動中..."
ssh "${REMOTE_HOST}" bash -s <<EOF
    set -euo pipefail
    cd ${REMOTE_DIR}
    docker-compose -f ${COMPOSE_FILE} down
    docker-compose -f ${COMPOSE_FILE} up -d
    echo "コンテナ起動完了。起動安定まで5秒待機..."
    sleep 5
EOF

# 5. 静的ファイルディレクトリの準備とマイグレーション
echo ""
echo "[5/7] 静的ファイルディレクトリの準備中..."
ssh "${REMOTE_HOST}" bash -s <<EOF
    set -euo pipefail
    cd ${REMOTE_DIR}
    # staticディレクトリが存在しない場合は作成
    if [ ! -d "static" ]; then
        echo "staticディレクトリを作成中..."
        mkdir -p static/app
        echo "# Static files directory" > static/.gitkeep
    fi
    # static_rootの内容をstaticにコピー（初回のみ）
    if [ -d "static_root/app" ] && [ ! "$(ls -A static/app)" ]; then
        echo "static_root/app から static/app にファイルをコピー中..."
        cp -r static_root/app/* static/app/ 2>/dev/null || true
    fi
EOF

# 6. マイグレーションと静的ファイル収集
echo ""
echo "[6/7] マイグレーションと静的ファイル収集を実行中..."
ssh "${REMOTE_HOST}" bash -s <<EOF
    set -euo pipefail
    cd ${REMOTE_DIR}
    docker-compose -f ${COMPOSE_FILE} exec -T gunicorn python manage.py migrate --noinput
    docker-compose -f ${COMPOSE_FILE} exec -T gunicorn python manage.py collectstatic --noinput
    # nginxを再起動して静的ファイルを再読み込み
    docker-compose -f ${COMPOSE_FILE} restart nginx
EOF

# 7. ヘルスチェック
echo ""
echo "[7/7] ヘルスチェック中..."
ssh "${REMOTE_HOST}" bash -s <<EOF
    set -euo pipefail
    cd ${REMOTE_DIR}

    # コンテナが正常に動作しているか確認
    if docker-compose -f ${COMPOSE_FILE} ps | grep -q "Up"; then
        echo "全コンテナが正常に稼働中です"
        docker-compose -f ${COMPOSE_FILE} ps
    else
        echo "エラー: コンテナが正常に起動していません"
        docker-compose -f ${COMPOSE_FILE} ps
        docker-compose -f ${COMPOSE_FILE} logs --tail=20
        exit 1
    fi
EOF

echo ""
echo "============================================"
echo " デプロイ完了!"
echo " ホスト: ${REMOTE_HOST}"
echo " ブランチ: ${BRANCH}"
echo "============================================"
