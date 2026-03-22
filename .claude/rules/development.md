- 開発環境は `docker-compose-dev.yml` を使用する
- Django の管理コマンドは gunicorn コンテナ内で実行すること

## ファイル変更後の反映手順

### Python / テンプレート / 設定ファイルを変更した場合
**`bash restart-dev.sh` を必ず実行すること**（コンテナ再起動 + collectstatic を一括実行）

### TypeScript (`src/ts/*.ts`) を編集した場合
以下の手順を必ず実行すること：
1. `npm run build` でコンパイル（`static/app/*.js` が更新される）
2. `docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py collectstatic --noinput` で静的ファイルを反映
- ※ `ManifestStaticFilesStorage` によりファイル名にハッシュが付与されるため、collectstatic を省略するとブラウザが古いJSを使い続ける

### CSS / JS など静的ファイルのみを変更した場合
`docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py collectstatic --noinput` のみ実行すること（コンテナ再起動不要）

## キャッシュについて
静的ファイルのURLにはコンテンツハッシュが付与される（例: `task.abc12345.js`）。
collectstatic を実行するたびにハッシュが更新されるため、ブラウザキャッシュを手動でクリアする必要はない。

```bash
# 再起動スクリプト（コンテナ再起動 + collectstatic を一括実行）
bash restart-dev.sh

# マイグレーション生成・適用
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py makemigrations
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py migrate

# その他の manage.py コマンド例
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py collectstatic
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py createsuperuser
```
