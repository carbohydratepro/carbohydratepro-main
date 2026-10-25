#!/usr/bin/env bash
# root所有の /usr/local/libexec/carbohydratepro/ へ配置してsystemdから実行する。
set -Eeuo pipefail
umask 077
CONFIG=/etc/carbohydratepro/origin-maintenance.env
CERT=/etc/letsencrypt/live/lightsail.carbohydratepro.com/fullchain.pem
IMAGE=certbot/dns-route53@sha256:38fdfaed25f1e2554b22b835d257756afcfe3acacb8f943ec0884c251e561130
REPO=/home/ec2-user/carbohydratepro
test "$EUID" = 0
test "$(stat -c '%u:%a' "$CONFIG")" = 0:600
exec 9>/run/carbohydratepro-certificate.lock
flock -n 9 || exit 0
failure() {
    logger -p daemon.err -t carbohydratepro-certificate 'Origin certificate renewal/check failed'
    printf 'ERROR %s origin_certificate 0 0 HTTPS証明書の更新・検証に失敗しました。systemd journalを確認してください。\n' \
        "$(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M:%S,%3N')" >> "$REPO/django_debug.log"
}
trap failure ERR
args=(renew --non-interactive --cert-name lightsail.carbohydratepro.com)
if [[ "${1:-}" == --dry-run ]]; then
    args+=(--dry-run)
elif [[ $# != 0 ]]; then
    echo 'Usage: renew-origin-certificate.sh [--dry-run]' >&2
    exit 2
fi
docker run --rm --env-file "$CONFIG" \
    -v /etc/letsencrypt:/etc/letsencrypt \
    -v /var/lib/letsencrypt:/var/lib/letsencrypt \
    -v /var/log/letsencrypt:/var/log/letsencrypt \
    "$IMAGE" "${args[@]}"
# 更新済み証明書が前回reload失敗で未反映の場合も再試行する。
docker exec nginx nginx -t
docker exec nginx nginx -s reload
openssl x509 -in "$CERT" -checkend 1209600 -noout
