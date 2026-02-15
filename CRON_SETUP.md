# 定期支払い自動実行の設定

## 概要

定期支払い機能は、毎日0時に自動的に実行されます。この自動実行はcronコンテナによって管理されています。

## 本番環境・ローカル環境共通の設定

### 構成

- **cronコンテナ**: `Dockerfile.cron` を使用してビルドされます
- **cron設定ファイル**: `crontab` に定期実行の設定が記載されています
- **実行時刻**: 毎日0時（UTC）
- **実行コマンド**: `python manage.py execute_recurring_payments`

### cronコンテナの起動

```bash
# 本番環境
docker-compose up -d

# ローカル環境
docker-compose -f docker-compose-dev.yml up -d
```

cronコンテナは自動的に起動し、バックグラウンドで動作します。

### cronログの確認

実行ログを確認するには、以下のコマンドを使用します：

```bash
# 本番環境
docker logs cron

# ローカル環境
docker-compose -f docker-compose-dev.yml logs cron

# リアルタイムでログを監視
docker logs -f cron
```

## ローカル環境でのテスト

ローカル環境では、cronの動作を待たずに手動でコマンドを実行してテストできます。

### 手動実行方法

```bash
# 本日分の定期支払いを手動実行
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py execute_recurring_payments

# 特定の日付で実行（YYYY-MM-DD形式）
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py execute_recurring_payments --date 2026-02-15
```

### cronスクリプトのテスト

cronコンテナ内でスクリプトを直接実行してテストすることもできます：

```bash
# cronコンテナに入る
docker-compose -f docker-compose-dev.yml exec cron bash

# コンテナ内で実行
cd /code
python manage.py execute_recurring_payments
```

## トラブルシューティング

### cronが実行されない場合

1. **cronコンテナの状態を確認**
   ```bash
   docker ps | grep cron
   ```

2. **cronログを確認**
   ```bash
   docker logs cron
   ```

3. **cron設定を確認**
   ```bash
   docker exec cron cat /etc/cron.d/recurring-payments
   ```

4. **cronデーモンの状態を確認**
   ```bash
   docker exec cron service cron status
   ```

### タイムゾーンについて

- cronコンテナはUTCタイムゾーンで動作します
- 日本時間（JST）で0時に実行したい場合は、crontabの設定を `0 15 * * *`（UTC 15:00 = JST 0:00）に変更してください

### 設定変更後の反映

crontabファイルや環境変数を変更した場合は、cronコンテナを再ビルド・再起動してください：

```bash
# 本番環境
docker-compose build cron
docker-compose up -d cron

# ローカル環境
docker-compose -f docker-compose-dev.yml build cron
docker-compose -f docker-compose-dev.yml up -d cron
```
