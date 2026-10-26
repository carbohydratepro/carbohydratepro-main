#!/usr/bin/env bash
# 本番のお問い合わせ（ContactMessage）を参照・ステータス更新する。
# 既定は読み取り専用。set-status だけが書き込みで、--yes がないと実行しない。
# 接続先・鍵・メールアドレスはこのスクリプトに書かない（環境変数で渡す）。
set -euo pipefail

REMOTE_HOST="${INQUIRY_SSH_HOST:-${DEPLOY_HOST:-}}"
SSH_CONFIG="${INQUIRY_SSH_CONFIG:-}"
REMOTE_DIR="carbohydratepro"
COMPOSE_FILE="docker-compose-dev.yml"

usage() {
    cat <<'EOF'
Usage:
  production-inquiries.sh [--host HOST] [--ssh-config FILE] list [--status open|in_progress|resolved|all] [--limit N]
  production-inquiries.sh [--host HOST] [--ssh-config FILE] show ID
  production-inquiries.sh [--host HOST] [--ssh-config FILE] set-status ID open|in_progress|resolved --yes

Environment:
  INQUIRY_SSH_HOST (または DEPLOY_HOST)  SSH接続先（ssh config の Host 別名を推奨）
  INQUIRY_SSH_CONFIG                    専用 ssh config を使う場合のパス

送信者はユーザーIDだけを表示し、メールアドレス等の個人情報は出力しない。
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --host) REMOTE_HOST="${2:?--host requires a value}"; shift 2 ;;
        --ssh-config) SSH_CONFIG="${2:?--ssh-config requires a value}"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) break ;;
    esac
done

ACTION="${1:-}"
[[ -n "${ACTION}" ]] || { usage; exit 1; }
shift

STATUS="open"
LIMIT="20"
CONTACT_ID=""
NEW_STATUS=""
CONFIRMED="0"

case "${ACTION}" in
    list)
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --status) STATUS="${2:?}"; shift 2 ;;
                --limit) LIMIT="${2:?}"; shift 2 ;;
                *) echo "エラー: 不明な引数です: $1" >&2; exit 1 ;;
            esac
        done
        [[ "${STATUS}" =~ ^(open|in_progress|resolved|all)$ ]] || { echo "エラー: --status が不正です" >&2; exit 1; }
        [[ "${LIMIT}" =~ ^[0-9]{1,3}$ ]] || { echo "エラー: --limit は1〜999で指定してください" >&2; exit 1; }
        ;;
    show)
        CONTACT_ID="${1:-}"
        ;;
    set-status)
        CONTACT_ID="${1:-}"
        NEW_STATUS="${2:-}"
        [[ "${3:-}" == "--yes" ]] && CONFIRMED="1"
        [[ "${NEW_STATUS}" =~ ^(open|in_progress|resolved)$ ]] || { echo "エラー: ステータスが不正です" >&2; exit 1; }
        if [[ "${CONFIRMED}" != "1" ]]; then
            echo "エラー: 本番データの更新です。ユーザーの承認を得てから --yes を付けて実行してください。" >&2
            exit 1
        fi
        ;;
    *) usage; exit 1 ;;
esac

if [[ -n "${CONTACT_ID}" && ! "${CONTACT_ID}" =~ ^[0-9]+$ ]]; then
    echo "エラー: ID は数値で指定してください" >&2
    exit 1
fi
[[ -n "${REMOTE_HOST}" ]] || { echo "エラー: --host または INQUIRY_SSH_HOST を指定してください。" >&2; exit 1; }

SSH_ARGS=()
[[ -n "${SSH_CONFIG}" ]] && SSH_ARGS+=(-F "${SSH_CONFIG}")

# Django shell で実行するコード。引数は環境変数で渡し、文字列連結でコードを組み立てない。
read -r -d '' PY_CODE <<'PY' || true
import os
from django.utils import timezone
from app.models import ContactMessage as C

action = os.environ["INQ_ACTION"]

def header(c):
    local = timezone.localtime(c.created_at).strftime("%Y-%m-%d %H:%M")
    return f"#{c.id} [{c.get_status_display()}] {c.get_inquiry_type_display()} {local} user_id={c.user_id} 件名: {c.subject}"

if action == "list":
    qs = C.objects.order_by("-created_at")
    status = os.environ["INQ_STATUS"]
    if status != "all":
        qs = qs.filter(status=status)
    print(f"件数: {qs.count()}")
    for c in qs[: int(os.environ["INQ_LIMIT"])]:
        print(header(c))
elif action == "show":
    c = C.objects.get(id=int(os.environ["INQ_ID"]))
    print(header(c))
    print("---- 本文 ----")
    print(c.message)
    print("---- 返信 ----")
    print(c.admin_reply or "(なし)")
elif action == "set-status":
    c = C.objects.get(id=int(os.environ["INQ_ID"]))
    before = c.status
    c.status = os.environ["INQ_NEW_STATUS"]
    c.is_resolved = c.status == "resolved"
    c.save(update_fields=["status", "is_resolved"])
    print(f"#{c.id}: {before} -> {c.status}")
PY

ENV_ARGS="-e INQ_ACTION=${ACTION} -e INQ_STATUS=${STATUS} -e INQ_LIMIT=${LIMIT} -e INQ_ID=${CONTACT_ID:-0} -e INQ_NEW_STATUS=${NEW_STATUS:-open}"

# shellcheck disable=SC2029  # ENV_ARGS は上で検証済みの値だけで構成している
ssh "${SSH_ARGS[@]}" "${REMOTE_HOST}" \
    "cd ${REMOTE_DIR} && docker-compose -f ${COMPOSE_FILE} exec -T ${ENV_ARGS} gunicorn python manage.py shell -c \"\$(cat)\"" \
    <<<"${PY_CODE}" 2> >(grep -v -e 'post-quantum' -e 'store now, decrypt later' -e 'openssh.com/pq.html' >&2)
