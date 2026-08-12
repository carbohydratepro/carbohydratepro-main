#!/usr/bin/env bash
set -euo pipefail

CRON_FILE="/etc/cron.d/carbohydratepro-docker-maintenance"
TEMP_CRON="$(mktemp)"
trap 'rm -f "${TEMP_CRON}"' EXIT

{
    echo 'SHELL=/bin/bash'
    echo 'PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin'
    echo
    echo '# 7日より古い未使用Docker資産を毎週日曜4:30 JST（土曜19:30 UTC）に削除'
    echo '30 19 * * 6 root docker image prune -a -f --filter until=168h && docker builder prune -a -f --filter until=168h >> /var/log/carbohydratepro-docker-maintenance.log 2>&1'
} > "${TEMP_CRON}"

sudo install -m 0644 "${TEMP_CRON}" "${CRON_FILE}"
echo "Docker定期保守cronを更新しました: ${CRON_FILE}"
