- 開発環境は `docker-compose-dev.yml` を使用する
- Django の管理コマンドは gunicorn コンテナ内で実行すること
- ファイルを変更した場合は `docker-compose -f docker-compose-dev.yml down && docker-compose -f docker-compose-dev.yml up -d` でコンテナを再起動すること
- TypeScript (`src/ts/*.ts`) を編集した場合は以下の手順を必ず実行すること：
  1. `npm run build` でコンパイル（`static/app/*.js` が更新される）
  2. `docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py collectstatic --noinput` で静的ファイルを反映
  - ※ コンテナ起動時に `collectstatic` は自動実行されないため、省略すると古いJSが配信され続ける

```bash
# コンテナのビルド・起動
docker-compose -f docker-compose-dev.yml build
docker-compose -f docker-compose-dev.yml up -d

# マイグレーション生成・適用
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py makemigrations
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py migrate

# その他の manage.py コマンド例
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py collectstatic
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py createsuperuser
```
