#!/usr/bin/env bash
# Config and baseline must be reviewed before enabling the timer. No network rules are changed.
set -Eeuo pipefail
if [[ "${EUID}" != 0 ]]; then echo 'rootで実行してください' >&2; exit 1; fi
root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
config=/etc/carbohydratepro/host-monitor.json
if [[ ! -f "${config}" ]]; then echo 'レビュー済みのhost-monitor.jsonを先に配置してください' >&2; exit 1; fi
install -d -m 0755 /usr/local/libexec/carbohydratepro
install -d -m 0700 /var/lib/carbohydratepro-monitor
install -m 0755 "${root_dir}/scripts/collect-host-security.py" /usr/local/libexec/carbohydratepro/
install -m 0644 "${root_dir}/scripts/systemd/carbohydratepro-security-monitor.service" /etc/systemd/system/
install -m 0644 "${root_dir}/scripts/systemd/carbohydratepro-security-monitor.timer" /etc/systemd/system/
# 有効化で作られるsymlinkも初回baselineへ含め、導入自身を改変と誤検知しない。
systemctl daemon-reload
systemctl enable carbohydratepro-security-monitor.timer
if [[ ! -f /var/lib/carbohydratepro-monitor/baseline.json ]]; then
    /usr/bin/python3 /usr/local/libexec/carbohydratepro/collect-host-security.py --initialize
fi
/usr/bin/python3 /usr/local/libexec/carbohydratepro/collect-host-security.py
systemctl start carbohydratepro-security-monitor.timer
