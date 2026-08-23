#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARCHIVE_SCRIPT="${REPO_ROOT}/scripts/archive-production-logs.sh"
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf -- "${TEST_ROOT}"' EXIT

create_fake_commands() {
    local case_dir="$1"
    mkdir -p "${case_dir}/bin" "${case_dir}/aws-state"

    cat > "${case_dir}/bin/aws" <<'FAKE_AWS'
#!/usr/bin/env bash
set -euo pipefail
operation="${1:-} ${2:-}"
shift 2
case "${operation}" in
    's3 cp')
        body="$1"
        shift 2
        metadata=''
        while (($#)); do
            case "$1" in
                --metadata) metadata="$2"; shift 2 ;;
                *) shift ;;
            esac
        done
        stat -c '%s' "${body}" > "${FAKE_AWS_STATE}/size"
        printf '%s\n' "${metadata#sha256=}" > "${FAKE_AWS_STATE}/sha256"
        ;;
    's3api head-object')
        if [[ "${FAKE_AWS_FAIL_VERIFY:-0}" == '1' ]]; then
            printf '0\tinvalid\tAES256\n'
        else
            printf '%s\t%s\tAES256\n' \
                "$(<"${FAKE_AWS_STATE}/size")" \
                "$(<"${FAKE_AWS_STATE}/sha256")"
        fi
        ;;
    *)
        echo "unexpected fake aws operation: ${operation}" >&2
        exit 1
        ;;
esac
FAKE_AWS

    cat > "${case_dir}/bin/journalctl" <<'FAKE_JOURNALCTL'
#!/usr/bin/env bash
set -euo pipefail
case " $* " in
    *' --vacuum-'*) touch "${FAKE_JOURNAL_STATE}/vacuumed" ;;
    *)
        printf '%s\n' "$*" >> "${FAKE_JOURNAL_STATE}/calls"
        printf '2026-08-23T00:00:00+0000 test journal entry\n'
        ;;
esac
FAKE_JOURNALCTL
    chmod +x "${case_dir}/bin/aws" "${case_dir}/bin/journalctl"
}

setup_case() {
    local case_name="$1" case_dir="${TEST_ROOT}/${1}"
    mkdir -p "${case_dir}/repo" "${case_dir}/state" "${case_dir}/journal-state"
    create_fake_commands "${case_dir}"
    cat > "${case_dir}/config.env" <<'CONFIG'
AWS_ACCESS_KEY_ID=test-access-key
AWS_SECRET_ACCESS_KEY=test-secret-key
AWS_DEFAULT_REGION=ap-northeast-1
LOG_ARCHIVE_BUCKET=test-bucket
LOG_ARCHIVE_PREFIX=production
LOG_ARCHIVE_INSTANCE=test-instance
CONFIG
    chmod 0600 "${case_dir}/config.env"
    touch "${case_dir}/state/bootstrap.done"
    printf '%s\n' '1787443200' > "${case_dir}/state/next-hour-epoch"
    printf 'active debug log\n' > "${case_dir}/repo/django_debug.log"
    printf 'active security log\n' > "${case_dir}/repo/security.log"
    printf 'rotated debug log\n' > "${case_dir}/repo/django_debug.log.1"
    printf '%s\n' "${case_dir}"
}

run_archive() {
    local case_dir="$1"
    LOG_ARCHIVE_CONFIG_FILE="${case_dir}/config.env" \
    LOG_ARCHIVE_STATE_DIR="${case_dir}/state" \
    LOG_ARCHIVE_REPO_DIR="${case_dir}/repo" \
    LOG_ARCHIVE_REQUIRE_ROOT=0 \
    LOG_ARCHIVE_NOW_EPOCH=1787443200 \
    AWS_BIN="${case_dir}/bin/aws" \
    JOURNALCTL_BIN="${case_dir}/bin/journalctl" \
    FAKE_AWS_STATE="${case_dir}/aws-state" \
    FAKE_JOURNAL_STATE="${case_dir}/journal-state" \
    FAKE_AWS_FAIL_VERIFY="${FAKE_AWS_FAIL_VERIFY:-0}" \
    "${ARCHIVE_SCRIPT}"
}

success_case="$(setup_case success)"
run_archive "${success_case}"
[[ ! -e "${success_case}/repo/django_debug.log.1" ]]
[[ -e "${success_case}/journal-state/vacuumed" ]]

catchup_case="$(setup_case catchup)"
rm -f "${catchup_case}/state/bootstrap.done"
printf '%s\n' '1787439600' > "${catchup_case}/state/next-hour-epoch"
run_archive "${catchup_case}" >/dev/null
[[ -s "${catchup_case}/state/bootstrap.done" ]]
[[ "$(<"${catchup_case}/state/next-hour-epoch")" == '1787443200' ]]
[[ -e "${catchup_case}/journal-state/vacuumed" ]]
rg -Fq -- '--since @1787439600 --until @1787443200' \
    "${catchup_case}/journal-state/calls"

failure_case="$(setup_case failure)"
set +e
FAKE_AWS_FAIL_VERIFY=1 run_archive "${failure_case}" >/dev/null 2>&1
failure_status=$?
set -e
[[ "${failure_status}" -ne 0 ]]
[[ -e "${failure_case}/repo/django_debug.log.1" ]]
rg -q 'S3ログアーカイブに失敗しました' "${failure_case}/repo/django_debug.log"
[[ ! -e "${failure_case}/journal-state/vacuumed" ]]

echo 'ログアーカイブスクリプトテスト: OK'
