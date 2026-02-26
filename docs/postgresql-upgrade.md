# PostgreSQL バージョンアップグレード手順

Docker Compose 環境で PostgreSQL のメジャーバージョンをアップグレードする手順です。
データファイルのフォーマットがメジャーバージョン間で非互換なため、バックアップ＆リストアが必要です。

## 前提条件

- `docker-compose-dev.yml` で PostgreSQL コンテナを管理している
- バックアップ先ディレクトリに十分な空き容量がある

## 手順

### 1. コンテナが起動していることを確認

```bash
docker-compose -f docker-compose-dev.yml ps
```

### 2. データベースをバックアップ

```bash
docker-compose -f docker-compose-dev.yml exec db \
  pg_dump -U myuser mydatabase > backup.sql
```

バックアップファイルのサイズを確認：

```bash
ls -lh backup.sql
```

> **重要**: バックアップファイルは安全な場所（リポジトリ外）に保管してください。

### 3. コンテナを停止（ボリュームは削除しない）

```bash
docker-compose -f docker-compose-dev.yml down
```

`docker-compose down -v` は使わないこと（ボリュームが削除されてしまう）。

### 4. `docker-compose-dev.yml` の PostgreSQL バージョンを更新

```yaml
# 変更前
image: postgres:13

# 変更後
image: postgres:16
```

### 5. 旧ボリュームを削除

```bash
docker volume rm carbohydratepro-main_postgres_data
```

### 6. 新バージョンの DB コンテナのみ起動

```bash
docker-compose -f docker-compose-dev.yml up -d db
sleep 5  # 初期化を待つ
```

### 7. バックアップをリストア

```bash
docker-compose -f docker-compose-dev.yml exec -T db \
  psql -U myuser mydatabase < backup.sql
```

### 8. 全コンテナを起動

```bash
docker-compose -f docker-compose-dev.yml up -d
```

### 9. 動作確認

```bash
# Django チェック
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py check

# テスト実行
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py test
```

## 実施履歴

| 日付       | 内容                        | 担当 |
|------------|-----------------------------|------|
| 2026-02-27 | PostgreSQL 13 → 16 アップグレード（Django 5.2 対応） | - |
