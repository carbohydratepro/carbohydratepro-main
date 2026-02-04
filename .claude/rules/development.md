- 開発環境は `docker-compose-dev.yml` を使用する
- Django の管理コマンドは gunicorn コンテナ内で実行すること
- ファイルを変更した場合は `docker-compose -f docker-compose-dev.yml down && docker-compose -f docker-compose-dev.yml up -d` でコンテナを再起動すること

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
