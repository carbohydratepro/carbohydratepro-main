#!/usr/bin/env bash
set -Eeuo pipefail

CONFIG_FILE="${LOG_ARCHIVE_CONFIG_FILE:-/etc/carbohydratepro/log-archive.env}"
STATE_DIR="${LOG_ARCHIVE_STATE_DIR:-/var/lib/carbohydratepro-log-archive}"
REPO_DIR="${LOG_ARCHIVE_REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
AWS_BIN="${AWS_BIN:-aws}"
JOURNALCTL_BIN="${JOURNALCTL_BIN:-journalctl}"
INITIAL_LOOKBACK_HOURS="${LOG_ARCHIVE_INITIAL_LOOKBACK_HOURS:-168}"
MAX_CATCHUP_HOURS="${LOG_ARCHIVE_MAX_CATCHUP_HOURS:-744}"
REQUIRE_ROOT="${LOG_ARCHIVE_REQUIRE_ROOT:-1}"

CURRENT_STAGE="初期化"
TEMP_DIR=""

log_message() {
    printf '%s %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"
}

record_failure_for_daily_report() {
    local now_epoch last_notice=0 notice_file
    now_epoch="$(date -u +%s)"
    notice_file="${STATE_DIR}/last-failure-notice-epoch"
    if [[ -f "${notice_file}" ]]; then
        read -r last_notice < "${notice_file}" || last_notice=0
    fi
    if [[ ! "${last_notice}" =~ ^[0-9]+$ ]] || (( now_epoch - last_notice >= 86400 )); then
        printf 'ERROR %s log_archive 0 0 S3ログアーカイブに失敗しました（処理: %s、詳細: /var/log/carbohydratepro-log-archive.log）\n' \
            "$(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M:%S,%3N')" \
            "${CURRENT_STAGE}" >> "${REPO_DIR}/django_debug.log"
        printf '%s\n' "${now_epoch}" > "${notice_file}"
        chmod 0600 "${notice_file}"
    fi
}

handle_error() {
    local status=$?
    trap - ERR
    set +e
    log_message "エラー: ${CURRENT_STAGE}に失敗しました（終了コード: ${status}）"
    record_failure_for_daily_report
    exit "${status}"
}

cleanup() {
    if [[ -n "${TEMP_DIR}" && -d "${TEMP_DIR}" ]]; then
        rm -rf -- "${TEMP_DIR}"
    fi
}

if [[ "${REQUIRE_ROOT}" == "1" && "${EUID}" -ne 0 ]]; then
    echo "エラー: rootで実行してください" >&2
    exit 1
fi

install -d -m 0700 "${STATE_DIR}"
exec 9> "${STATE_DIR}/archive.lock"
if ! flock -n 9; then
    log_message "別のログアーカイブ処理が実行中のため終了します"
    exit 0
fi

TEMP_DIR="$(mktemp -d)"
trap cleanup EXIT
trap handle_error ERR

CURRENT_STAGE="設定ファイルの確認"
if [[ ! -f "${CONFIG_FILE}" ]]; then
    echo "エラー: ${CONFIG_FILE} がありません" >&2
    false
fi
if [[ "${REQUIRE_ROOT}" == "1" ]]; then
    config_owner="$(stat -c '%u' "${CONFIG_FILE}")"
    config_mode="$(stat -c '%a' "${CONFIG_FILE}")"
    if [[ "${config_owner}" != "0" || "${config_mode}" != "600" ]]; then
        echo "エラー: ${CONFIG_FILE} はroot所有・0600にしてください" >&2
        false
    fi
fi

set -a
# shellcheck disable=SC1090
source "${CONFIG_FILE}"
set +a

: "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID が設定されていません}"
: "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY が設定されていません}"
: "${AWS_DEFAULT_REGION:?AWS_DEFAULT_REGION が設定されていません}"
: "${LOG_ARCHIVE_BUCKET:?LOG_ARCHIVE_BUCKET が設定されていません}"
: "${LOG_ARCHIVE_PREFIX:?LOG_ARCHIVE_PREFIX が設定されていません}"
: "${LOG_ARCHIVE_INSTANCE:?LOG_ARCHIVE_INSTANCE が設定されていません}"

if [[ ! "${LOG_ARCHIVE_INSTANCE}" =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "エラー: LOG_ARCHIVE_INSTANCE に使用できない文字があります" >&2
    false
fi
LOG_ARCHIVE_PREFIX="${LOG_ARCHIVE_PREFIX#/}"
LOG_ARCHIVE_PREFIX="${LOG_ARCHIVE_PREFIX%/}"
BASE_KEY="${LOG_ARCHIVE_PREFIX}/${LOG_ARCHIVE_INSTANCE}"

upload_and_verify() {
    local source_file="$1" object_key="$2"
    local local_size local_sha remote_values remote_size remote_sha remote_encryption

    local_size="$(stat -c '%s' "${source_file}")"
    local_sha="$(sha256sum "${source_file}" | awk '{print $1}')"

    "${AWS_BIN}" s3 cp \
        "${source_file}" \
        "s3://${LOG_ARCHIVE_BUCKET}/${object_key}" \
        --region "${AWS_DEFAULT_REGION}" \
        --sse AES256 \
        --metadata "sha256=${local_sha}" >/dev/null

    remote_values="$("${AWS_BIN}" s3api head-object \
        --region "${AWS_DEFAULT_REGION}" \
        --bucket "${LOG_ARCHIVE_BUCKET}" \
        --key "${object_key}" \
        --query '[ContentLength,Metadata.sha256,ServerSideEncryption]' \
        --output text)"
    read -r remote_size remote_sha remote_encryption <<< "${remote_values}"

    if [[ "${remote_size}" != "${local_size}" || "${remote_sha}" != "${local_sha}" || "${remote_encryption}" != "AES256" ]]; then
        echo "エラー: S3検証不一致: ${object_key}" >&2
        false
    fi
    log_message "S3転送・検証完了: ${object_key} (${local_size} bytes)"
}

archive_bootstrap_journal() {
    local archive_file object_key created_at
    if [[ -f "${STATE_DIR}/bootstrap.done" ]]; then
        return
    fi

    CURRENT_STAGE="既存system journalの初回アーカイブ"
    created_at="$(date -u '+%Y%m%dT%H%M%SZ')"
    archive_file="${TEMP_DIR}/bootstrap-${created_at}.journal.log.gz"
    "${JOURNALCTL_BIN}" --no-pager --output=short-iso | gzip -6 > "${archive_file}"
    object_key="${BASE_KEY}/system-journal/bootstrap/${created_at}.journal.log.gz"
    upload_and_verify "${archive_file}" "${object_key}"
    printf '%s\n' "${object_key}" > "${STATE_DIR}/bootstrap.done"
    chmod 0600 "${STATE_DIR}/bootstrap.done"
}

archive_completed_journal_hours() {
    local now_epoch completed_end cursor gap_hours next_cursor
    local start_text end_text hour_path archive_file object_key cursor_tmp

    now_epoch="${LOG_ARCHIVE_NOW_EPOCH:-$(date -u +%s)}"
    completed_end=$((now_epoch / 3600 * 3600))
    if [[ ! -f "${STATE_DIR}/next-hour-epoch" ]]; then
        cursor=$((completed_end - INITIAL_LOOKBACK_HOURS * 3600))
        printf '%s\n' "${cursor}" > "${STATE_DIR}/next-hour-epoch"
        chmod 0600 "${STATE_DIR}/next-hour-epoch"
    fi
    read -r cursor < "${STATE_DIR}/next-hour-epoch"
    if [[ ! "${cursor}" =~ ^[0-9]+$ ]] || (( cursor > completed_end )); then
        echo "エラー: 不正なjournal進捗値です: ${cursor}" >&2
        false
    fi

    gap_hours=$(((completed_end - cursor) / 3600))
    if (( gap_hours > MAX_CATCHUP_HOURS )); then
        echo "エラー: 未転送期間が上限${MAX_CATCHUP_HOURS}時間を超えています" >&2
        false
    fi

    while (( cursor < completed_end )); do
        next_cursor=$((cursor + 3600))
        start_text="$(date -u -d "@${cursor}" '+%Y-%m-%d %H:%M:%S UTC')"
        end_text="$(date -u -d "@${next_cursor}" '+%Y-%m-%d %H:%M:%S UTC')"
        hour_path="$(date -u -d "@${cursor}" '+%Y/%m/%d/%H')"
        archive_file="${TEMP_DIR}/journal-${cursor}.log.gz"
        object_key="${BASE_KEY}/system-journal/hourly/${hour_path}.journal.log.gz"

        CURRENT_STAGE="system journal ${start_text}～${end_text}のアーカイブ"
        "${JOURNALCTL_BIN}" \
            --since "${start_text}" \
            --until "${end_text}" \
            --no-pager \
            --output=short-iso | gzip -6 > "${archive_file}"
        upload_and_verify "${archive_file}" "${object_key}"

        cursor_tmp="${STATE_DIR}/next-hour-epoch.tmp"
        printf '%s\n' "${next_cursor}" > "${cursor_tmp}"
        chmod 0600 "${cursor_tmp}"
        mv -f -- "${cursor_tmp}" "${STATE_DIR}/next-hour-epoch"
        cursor="${next_cursor}"
    done
}

archive_active_application_logs() {
    local source_file base_name archive_file object_key snapshot_hour
    snapshot_hour="$(date -u -d "@${LOG_ARCHIVE_NOW_EPOCH:-$(date -u +%s)}" '+%Y/%m/%d/%H')"

    for base_name in django_debug.log security.log; do
        source_file="${REPO_DIR}/${base_name}"
        [[ -f "${source_file}" ]] || continue
        CURRENT_STAGE="${base_name}の時間スナップショット"
        archive_file="${TEMP_DIR}/${base_name}.gz"
        gzip -6 -c -- "${source_file}" > "${archive_file}"
        object_key="${BASE_KEY}/application/hourly/${snapshot_hour}/${base_name}.gz"
        upload_and_verify "${archive_file}" "${object_key}"
    done
}

archive_rotated_application_logs() {
    local source_file base_name before_signature after_signature mtime archive_file sha object_key

    while IFS= read -r -d '' source_file; do
        base_name="$(basename "${source_file}")"
        CURRENT_STAGE="${base_name}のローテーションアーカイブ"
        before_signature="$(stat -Lc '%d:%i:%s:%Y' "${source_file}")"
        mtime="$(stat -c '%Y' "${source_file}")"
        archive_file="${TEMP_DIR}/${base_name}-${mtime}.gz"
        gzip -6 -c -- "${source_file}" > "${archive_file}"
        sha="$(sha256sum "${archive_file}" | awk '{print $1}')"
        object_key="${BASE_KEY}/application/rotated/${base_name}/${mtime}-${sha}.gz"
        upload_and_verify "${archive_file}" "${object_key}"

        if [[ -f "${source_file}" ]]; then
            after_signature="$(stat -Lc '%d:%i:%s:%Y' "${source_file}")"
            if [[ "${before_signature}" == "${after_signature}" ]]; then
                rm -f -- "${source_file}"
                log_message "S3検証済みローテーションログをローカル削除: ${base_name}"
            else
                log_message "転送中に更新されたためローカル保持: ${base_name}"
            fi
        fi
    done < <(
        find "${REPO_DIR}" -maxdepth 1 -type f \
            \( -name 'django_debug.log.[0-9]*' -o -name 'security.log.[0-9]*' \) \
            -print0
    )
}

vacuum_uploaded_journal() {
    CURRENT_STAGE="転送済みsystem journalのローカル整理"
    "${JOURNALCTL_BIN}" --vacuum-time=7d --vacuum-size=1G
}

archive_bootstrap_journal
archive_completed_journal_hours
archive_active_application_logs
archive_rotated_application_logs
vacuum_uploaded_journal
CURRENT_STAGE="完了"
log_message "ログアーカイブ処理が正常終了しました"
