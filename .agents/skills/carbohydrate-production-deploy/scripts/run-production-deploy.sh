#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

REMOTE_HOST="${DEPLOY_HOST:-}"
BRANCH="main"
REMOTE_DIR="carbohydratepro"
COMPOSE_FILE="docker-compose-dev.yml"

usage() {
    cat <<'EOF'
Usage:
  run-production-deploy.sh --host user@host [--branch main] [--remote-dir carbohydratepro]

Environment:
  DEPLOY_HOST may be used instead of --host.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --host)
            REMOTE_HOST="${2:?--host requires a value}"
            shift 2
            ;;
        --branch)
            BRANCH="${2:?--branch requires a value}"
            shift 2
            ;;
        --remote-dir)
            REMOTE_DIR="${2:?--remote-dir requires a value}"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "エラー: 不明な引数です: $1" >&2
            usage
            exit 1
            ;;
    esac
done

if [[ -z "${REMOTE_HOST}" ]]; then
    echo "エラー: --host または DEPLOY_HOST を指定してください。" >&2
    exit 1
fi

cd "${REPO_ROOT}"

for command_name in git ssh md5sum sed awk; do
    if ! command -v "${command_name}" >/dev/null 2>&1; then
        echo "エラー: 必須コマンドがありません: ${command_name}" >&2
        exit 1
    fi
done

if [[ ! -f "${COMPOSE_FILE}" ]]; then
    echo "エラー: ${COMPOSE_FILE} が見つかりません。" >&2
    exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
    echo "エラー: 未コミット変更があります。デプロイ前に整理してください。" >&2
    git status --short >&2
    exit 1
fi

LOCAL_COMMIT="$(git rev-parse HEAD)"
echo "============================================"
echo " デプロイ対象"
echo " ホスト: ${REMOTE_HOST}"
echo " ブランチ: ${BRANCH}"
echo " ローカルコミット: ${LOCAL_COMMIT}"
echo " Compose: ${COMPOSE_FILE}（本番で意図的に使用）"
echo "============================================"

read -r -p "本番デプロイを実行しますか？ (yes/NO): " confirm
if [[ "${confirm}" != "yes" ]]; then
    echo "デプロイを中止しました。"
    exit 1
fi

ssh "${REMOTE_HOST}" \
    "REMOTE_DIR=$(printf '%q' "${REMOTE_DIR}") BRANCH=$(printf '%q' "${BRANCH}") COMPOSE_FILE=$(printf '%q' "${COMPOSE_FILE}") bash -s" <<'REMOTE_UPDATE'
set -euo pipefail
cd "${REMOTE_DIR}"
git fetch origin
git checkout "${BRANCH}"
git pull --ff-only origin "${BRANCH}"
echo "本番コミット: $(git rev-parse HEAD)"
docker-compose -f "${COMPOSE_FILE}" build
mkdir -p static_root
docker-compose -f "${COMPOSE_FILE}" down
docker-compose -f "${COMPOSE_FILE}" up -d

for attempt in $(seq 1 30); do
    if docker-compose -f "${COMPOSE_FILE}" exec -T gunicorn python -c \
        "import django; django.setup(); print('ready')" 2>/dev/null | grep -q "ready"; then
        echo "gunicorn準備完了（${attempt}秒）"
        break
    fi
    if [[ "${attempt}" -eq 30 ]]; then
        docker-compose -f "${COMPOSE_FILE}" logs --tail=50 gunicorn
        exit 1
    fi
    sleep 1
done

docker-compose -f "${COMPOSE_FILE}" exec -T gunicorn python manage.py migrate --noinput
docker-compose -f "${COMPOSE_FILE}" exec -T gunicorn python manage.py collectstatic --noinput
REMOTE_UPDATE

if ! compgen -G "static/app/*.js" >/dev/null; then
    echo "エラー: ローカルの static/app/*.js が見つかりません。" >&2
    exit 1
fi

LOCAL_HASHES="$(cd static/app && md5sum ./*.js | sed 's|\./||')"
REMOTE_HASHES="$(ssh "${REMOTE_HOST}" \
    "cd $(printf '%q' "${REMOTE_DIR}")/static_root/app && md5sum ./*.js 2>/dev/null | sed 's|\./||'")"

HASH_ERRORS=0
while IFS=' ' read -r local_hash filename; do
    remote_hash="$(printf '%s\n' "${REMOTE_HASHES}" | awk -v file="${filename}" '$2 == file { print $1 }')"
    if [[ -z "${remote_hash}" ]]; then
        echo "NG ${filename}: 本番に存在しません。"
        HASH_ERRORS=$((HASH_ERRORS + 1))
    elif [[ "${local_hash}" != "${remote_hash}" ]]; then
        echo "NG ${filename}: ハッシュが一致しません。"
        HASH_ERRORS=$((HASH_ERRORS + 1))
    else
        echo "OK ${filename}"
    fi
done <<< "${LOCAL_HASHES}"

if [[ "${HASH_ERRORS}" -gt 0 ]]; then
    echo "エラー: ${HASH_ERRORS}件の静的ファイル検証に失敗しました。" >&2
    exit 1
fi

ssh "${REMOTE_HOST}" \
    "REMOTE_DIR=$(printf '%q' "${REMOTE_DIR}") COMPOSE_FILE=$(printf '%q' "${COMPOSE_FILE}") bash -s" <<'REMOTE_VERIFY'
set -euo pipefail
cd "${REMOTE_DIR}"
docker-compose -f "${COMPOSE_FILE}" restart nginx
docker-compose -f "${COMPOSE_FILE}" ps

for file in app.js task.js transaction.js styles.css; do
    status="$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/static/app/${file}")"
    if [[ "${status}" != "200" ]]; then
        echo "エラー: /static/app/${file} (${status})" >&2
        exit 1
    fi
    echo "OK /static/app/${file} (${status})"
done
REMOTE_VERIFY

echo "デプロイ完了: ${REMOTE_HOST} ${BRANCH}"
