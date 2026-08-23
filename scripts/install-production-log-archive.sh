#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCHIVE_SCRIPT="${SCRIPT_DIR}/archive-production-logs.sh"
CONFIG_FILE="/etc/carbohydratepro/log-archive.env"
CRON_FILE="/etc/cron.d/carbohydratepro-log-archive"
LOGROTATE_FILE="/etc/logrotate.d/carbohydratepro-maintenance"
TEMP_CRON="$(mktemp)"
TEMP_LOGROTATE="$(mktemp)"
trap 'rm -f "${TEMP_CRON}" "${TEMP_LOGROTATE}"' EXIT

if [[ ! -x "${ARCHIVE_SCRIPT}" ]]; then
    echo "エラー: 実行可能なアーカイブスクリプトがありません: ${ARCHIVE_SCRIPT}" >&2
    exit 1
fi
if ! sudo test -f "${CONFIG_FILE}"; then
    echo "エラー: root専用のS3設定ファイルがありません: ${CONFIG_FILE}" >&2
    exit 1
fi
if [[ "$(sudo stat -c '%u:%a' "${CONFIG_FILE}")" != "0:600" ]]; then
    echo "エラー: ${CONFIG_FILE} はroot所有・0600にしてください" >&2
    exit 1
fi

{
    echo 'SHELL=/bin/bash'
    echo 'PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin'
    echo
    echo '# 完了した時間帯のsystem journal・アプリログを毎時S3へ退避'
    printf '10 * * * * root %q >> /var/log/carbohydratepro-log-archive.log 2>&1\n' "${ARCHIVE_SCRIPT}"
} > "${TEMP_CRON}"

{
    echo '/var/log/carbohydratepro-log-archive.log /var/log/carbohydratepro-docker-maintenance.log {'
    echo '    weekly'
    echo '    rotate 8'
    echo '    compress'
    echo '    delaycompress'
    echo '    missingok'
    echo '    notifempty'
    echo '    copytruncate'
    echo '}'
} > "${TEMP_LOGROTATE}"

sudo install -m 0644 "${TEMP_CRON}" "${CRON_FILE}"
sudo install -m 0644 "${TEMP_LOGROTATE}" "${LOGROTATE_FILE}"
echo "ログアーカイブcronを更新しました: ${CRON_FILE}"
