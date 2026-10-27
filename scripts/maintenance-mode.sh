#!/usr/bin/env bash
# メンテナンスモードの切替。本番サーバーのリポジトリ直下で実行する。
#   on     : .env を MAINTENANCE_MODE=True にして gunicorn を作り直す
#   off    : .env を MAINTENANCE_MODE=False にして gunicorn を作り直す
#   status : .env の値と、Django が実際に読んでいる値を表示する
# 環境変数の変更は restart では反映されないため、up -d で gunicorn だけを作り直す。
set -Eeuo pipefail

COMPOSE_FILE="docker-compose-dev.yml"
ENV_FILE=".env"
mode="${1:-status}"

cd "$(dirname "${BASH_SOURCE[0]}")/.."

effective_value() {
    docker-compose -f "${COMPOSE_FILE}" exec -T gunicorn python -c \
        'import django; django.setup(); from django.conf import settings; print(settings.MAINTENANCE_MODE)' </dev/null \
        | tr -d '\r' | tail -n 1
}

set_env_value() {
    local value="$1"
    touch "${ENV_FILE}"
    if grep -q '^MAINTENANCE_MODE=' "${ENV_FILE}"; then
        sed -i "s/^MAINTENANCE_MODE=.*/MAINTENANCE_MODE=${value}/" "${ENV_FILE}"
    else
        printf 'MAINTENANCE_MODE=%s\n' "${value}" >>"${ENV_FILE}"
    fi
}

wait_until() {
    local expected="$1" actual=""
    for _ in $(seq 1 30); do
        actual="$(effective_value 2>/dev/null || true)"
        if [[ "${actual}" == "${expected}" ]]; then
            echo "メンテナンスモード: ${actual}（Django設定で確認）"
            return 0
        fi
        sleep 2
    done
    echo "エラー: Django の MAINTENANCE_MODE が ${expected} になりません（現在: ${actual:-取得不可}）" >&2
    return 1
}

case "${mode}" in
    on|off)
        value="$([[ "${mode}" == "on" ]] && echo True || echo False)"
        set_env_value "${value}"
        docker-compose -f "${COMPOSE_FILE}" up -d --no-deps gunicorn
        wait_until "${value}"
        ;;
    status)
        echo ".env: $(grep '^MAINTENANCE_MODE=' "${ENV_FILE}" 2>/dev/null || echo '未設定（False扱い）')"
        echo "Django: $(effective_value)"
        ;;
    *)
        echo "Usage: $0 on|off|status" >&2
        exit 1
        ;;
esac
