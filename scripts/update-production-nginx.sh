#!/usr/bin/env bash
# 本番の現行リリースに対するNginxのみの更新。既定は事前確認のみ。
set -Eeuo pipefail

mode="${1:---check}"
if [[ "${mode}" != '--check' && "${mode}" != '--apply' ]]; then
    echo 'usage: bash update-production-nginx.sh [--check|--apply]' >&2
    exit 2
fi

repo_dir="${NGINX_UPDATE_REPO_DIR:-/home/ec2-user/carbohydratepro}"
expected_commit='8b294bdc156f9965d6ef4ddb8b58ee150778844a'
new_image='nginx:1.30.6@sha256:a7675fcee220f59b4a99f7098c06a0d5d999c2c0ee37c0211efb780536e5cb20'
cd "${repo_dir}"
[[ "$(git rev-parse HEAD)" == "${expected_commit}" ]] || {
    echo '本番コミットが準備時から変更されています。再確認してください。' >&2
    exit 1
}
git diff --quiet
git diff --cached --quiet
[[ "$(docker inspect --format '{{.Config.Image}}' nginx)" == 'nginx:1.17.7' ]]
docker image inspect "${new_image}" >/dev/null
docker run --rm --volumes-from nginx:ro "${new_image}" nginx -t
python3 - <<'PY'
from pathlib import Path
text = Path('docker-compose-dev.yml').read_text()
assert text.count('    image: nginx:1.17.7\n') == 1, 'Nginx設定を再確認してください'
PY

echo "対象: ${repo_dir} main ${expected_commit}"
echo "変更: nginx:1.17.7 -> ${new_image}"
echo '実行: docker-compose -f docker-compose-dev.yml up -d --no-deps --no-build nginx'
if [[ "${mode}" == '--check' ]]; then
    echo '事前確認完了。本番の設定・稼働コンテナは変更していません。'
    exit 0
fi

backup_dir="$(mktemp -d /home/ec2-user/nginx-update-backup-XXXXXXXX)"
chmod 700 "${backup_dir}"
cp -p docker-compose-dev.yml "${backup_dir}/docker-compose-dev.yml"
docker inspect --format '{{.Name}} {{.Id}}' gunicorn cron carbohydratepro-db-1 > "${backup_dir}/other-containers.txt"
echo "復旧用設定: ${backup_dir}/docker-compose-dev.yml"
trap 'echo "更新または検証に失敗しました。自動復旧は行いません。バックアップ: ${backup_dir}" >&2' ERR

python3 - "${new_image}" <<'PY'
import sys
from pathlib import Path
path = Path('docker-compose-dev.yml')
text = path.read_text()
old = '    image: nginx:1.17.7\n'
assert text.count(old) == 1
path.write_text(text.replace(old, '    image: ' + sys.argv[1] + '\n', 1))
PY
git diff -- docker-compose-dev.yml
docker-compose -f docker-compose-dev.yml up -d --no-deps --no-build nginx
docker exec nginx nginx -t
[[ "$(docker inspect --format '{{.Config.Image}}' nginx)" == "${new_image}" ]]
for path in / /login/ /static/app/styles.css /static/app/app.js; do
    curl --fail --silent --show-error --retry 5 --retry-connrefused --retry-delay 1 \
        --max-time 10 --output /dev/null "http://127.0.0.1:8000${path}"
    echo "OK ${path}"
done
docker inspect --format '{{.Name}} {{.Id}}' gunicorn cron carbohydratepro-db-1 > "${backup_dir}/other-containers-after.txt"
cmp "${backup_dir}/other-containers.txt" "${backup_dir}/other-containers-after.txt"
docker exec nginx nginx -v
echo 'Nginx更新完了。外部からCloudFront経由の応答も確認してください。'
