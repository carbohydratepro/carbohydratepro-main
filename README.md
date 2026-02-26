# carbohydratepro

個人向けのライフ管理 Web アプリケーション。家計簿・タスク管理・メモ・買い物リストなどの日常管理機能を提供します。

## 機能

| 機能 | 概要 |
|---|---|
| 家計簿 | 収支の記録・グラフ表示・カテゴリ管理 |
| 定期支払い | 毎日・毎週・毎月・毎年の定期支払いを自動記録（cron） |
| タスク管理 | スケジュール管理・繰り返しタスク・カンバンボード |
| メモ | マークダウン対応のメモ帳・お気に入り機能 |
| 買い物リスト | 個数管理付きの買い物リスト |
| ログ監視 | セキュリティ・エラーログの定期チェックとメール通知 |

## 使用技術

| 種別 | 名称 | バージョン |
|---|---|---|
| フレームワーク | Django | 5.2 |
| 言語 | Python | 3.12 |
| 言語 | JavaScript | - |
| 言語 | HTML / CSS | - |
| ライブラリ | Bootstrap | - |
| REST API | Django REST Framework | - |
| データベース | PostgreSQL | 16 |
| Web サーバー | Nginx | 1.17.7 |
| WSGI サーバー | Gunicorn | 最新 |
| インフラ | Docker / Docker Compose | - |
| クラウド | Amazon Lightsail | - |

## 開発環境のセットアップ

### 前提条件

- Docker / Docker Compose がインストール済みであること
- SSH 鍵認証が設定済みであること（本番操作時）

### 起動

```bash
# ビルド
docker-compose -f docker-compose-dev.yml build

# 起動
docker-compose -f docker-compose-dev.yml up -d

# 停止
docker-compose -f docker-compose-dev.yml down
```

### マイグレーション・管理コマンド

```bash
# マイグレーション生成
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py makemigrations

# マイグレーション適用
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py migrate

# 静的ファイル収集
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py collectstatic

# スーパーユーザー作成
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py createsuperuser

# テスト実行
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py test
```

### ログ確認

```bash
# gunicorn ログ
docker-compose -f docker-compose-dev.yml logs gunicorn

# cron ログ（定期実行・ログ監視）
docker-compose -f docker-compose-dev.yml logs -f cron
```

## デプロイ

`deploy.sh`（gitignore 対象、各自のローカルに配置）を使用します。

```bash
# 本番サーバーに main ブランチをデプロイ
./deploy.sh

# ブランチを指定してデプロイ
./deploy.sh develop
```

デプロイスクリプトは以下を自動実行します：

1. ローカルの未コミット変更確認
2. リモートサーバーで `git pull`
3. Docker イメージのビルド
4. コンテナ再起動
5. `migrate` / `collectstatic`
6. ヘルスチェック

## 本番サーバーの初回セットアップ

Amazon Linux 2 (EC2 / Lightsail) での環境構築手順です。

```bash
# Docker インストール
sudo yum update -y
sudo amazon-linux-extras install docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Docker Compose インストール
sudo curl -L "https://github.com/docker/compose/releases/download/v2.11.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Git インストール・リポジトリのクローン
sudo yum install git -y
git clone [project URL]
cd carbohydratepro
```

権限エラーが出る場合：

```bash
sudo usermod -aG docker ec2-user
newgrp docker
sudo systemctl restart docker
```

### スワップ領域の追加（メモリ 1GB 環境向け）

```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 再起動後も有効にする
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 確認
free -h
```

## PostgreSQL バージョンアップグレード

メジャーバージョンアップ時はバックアップ＆リストアが必要です。詳細は [`docs/postgresql-upgrade.md`](docs/postgresql-upgrade.md) を参照してください。

## ログ監視

セキュリティログ・エラーログの監視は cron コンテナが自動実行します。設定の詳細は [`SECURITY_MONITORING_SETUP.md`](SECURITY_MONITORING_SETUP.md) を参照してください。

## 定期支払いの自動実行

定期支払いは cron コンテナが毎日 0 時（JST）に自動実行します。設定の詳細は [`CRON_SETUP.md`](CRON_SETUP.md) を参照してください。
