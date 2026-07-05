#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
COMPOSE_FILE="${REPO_ROOT}/docker-compose-dev.yml"

cd "${REPO_ROOT}"

compose=()
if command -v docker-compose >/dev/null 2>&1 && docker-compose version >/dev/null 2>&1; then
    compose=(docker-compose)
elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    compose=(docker compose)
fi

usage() {
    cat <<'EOF'
Usage:
  manage-dev-environment.sh doctor
  manage-dev-environment.sh start
  manage-dev-environment.sh stop
  manage-dev-environment.sh restart
  manage-dev-environment.sh build
  manage-dev-environment.sh rebuild
  manage-dev-environment.sh status
  manage-dev-environment.sh logs [service]
  manage-dev-environment.sh check
  manage-dev-environment.sh makemigrations [app-label ...]
  manage-dev-environment.sh migrate
  manage-dev-environment.sh collectstatic
  manage-dev-environment.sh createsuperuser
  manage-dev-environment.sh test [django-test-label ...]
  manage-dev-environment.sh shell
EOF
}

require_compose() {
    if [[ ${#compose[@]} -eq 0 ]]; then
        echo "エラー: docker-compose または docker compose を利用できません。" >&2
        echo "Docker Desktopを使う場合は、archlinuxへのWSL integrationを有効にしてください。" >&2
        exit 1
    fi
}

run_compose() {
    require_compose
    "${compose[@]}" -f "${COMPOSE_FILE}" "$@"
}

wait_for_gunicorn() {
    local attempt
    for attempt in $(seq 1 30); do
        if run_compose exec -T gunicorn python -c \
            "import django; django.setup(); print('ready')" 2>/dev/null | grep -q "ready"; then
            echo "gunicorn準備完了（${attempt}秒）"
            return 0
        fi
        sleep 1
    done

    echo "エラー: gunicornが30秒以内に準備完了しませんでした。" >&2
    run_compose logs --tail=50 gunicorn >&2 || true
    return 1
}

action="${1:-}"
if [[ -z "${action}" ]]; then
    usage
    exit 1
fi
shift

case "${action}" in
    -h|--help|help)
        usage
        ;;
    doctor)
        if [[ ! -f "${COMPOSE_FILE}" ]]; then
            echo "エラー: ${COMPOSE_FILE} が見つかりません。" >&2
            exit 1
        fi
        require_compose
        echo "リポジトリ: ${REPO_ROOT}"
        echo "Compose: ${compose[*]}"
        "${compose[@]}" version
        ;;
    start)
        run_compose up -d
        wait_for_gunicorn
        run_compose ps
        ;;
    stop)
        run_compose down
        ;;
    restart)
        run_compose down
        run_compose up -d
        wait_for_gunicorn
        run_compose exec -T gunicorn python manage.py collectstatic --noinput
        run_compose ps
        ;;
    build)
        run_compose build
        ;;
    rebuild)
        run_compose build
        run_compose down
        run_compose up -d
        wait_for_gunicorn
        run_compose exec -T gunicorn python manage.py collectstatic --noinput
        run_compose ps
        ;;
    status)
        run_compose ps
        ;;
    logs)
        if [[ $# -gt 0 ]]; then
            run_compose logs --tail=200 -f "$1"
        else
            run_compose logs --tail=200 -f
        fi
        ;;
    check)
        run_compose exec -T gunicorn python manage.py check
        ;;
    makemigrations)
        run_compose exec -T gunicorn python manage.py makemigrations "$@"
        ;;
    migrate)
        run_compose exec -T gunicorn python manage.py migrate
        ;;
    collectstatic)
        run_compose exec -T gunicorn python manage.py collectstatic --noinput
        ;;
    createsuperuser)
        run_compose exec gunicorn python manage.py createsuperuser
        ;;
    test)
        run_compose exec -T gunicorn python manage.py test "$@"
        ;;
    shell)
        run_compose exec gunicorn bash
        ;;
    *)
        echo "エラー: 未対応の操作です: ${action}" >&2
        usage
        exit 1
        ;;
esac
