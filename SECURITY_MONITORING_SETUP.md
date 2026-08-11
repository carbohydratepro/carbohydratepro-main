# ログ監視設定ガイド

## 概要
このシステムは以下のログファイルを監視し、問題が検知された場合にメール通知を送信します：

1. **security.log**: セキュリティイベント（管理者ログイン、不正アクセス試行など）
2. **django_debug.log**: アプリケーションの重大ログ（ERROR、CRITICAL）

これらを毎日6時（JST）に集約し、対象がある場合だけ1通のレポートを送信します。
管理画面探索、CSRF拒否、存在しないアカウントへのログイン試行などの日常的な
インターネットノイズは件数のみを記載します。

## 本番環境・ローカル環境（Docker環境）

**重要**: 現在、監視スクリプトはDockerのcronコンテナで自動実行されます。

### 自動実行の仕組み

監視スクリプトは定期支払い機能と同じcronコンテナで実行されます：
- `crontab` ファイルに設定が記載されています
- コンテナ起動時に自動的に監視が開始されます
- 手動設定は不要です

## 機能
1. **リアルタイム通知**: 管理者・スタッフがログインした際に即座にメール送信（オプション）
2. **日次セキュリティ監視**: 過去24時間のsecurity.logを分類・集約
3. **重大エラー監視**: ERRORとCRITICALだけを日次レポートへ統合（WARNINGはメール対象外）

## セットアップ方法

### Docker環境（本番・ローカル共通）

監視機能は既にcronコンテナに統合されています。以下の手順で有効化できます：

#### 1. コンテナの再起動

監視機能を有効化するには、cronコンテナを再起動してください：

```bash
docker-compose -f docker-compose-dev.yml build cron
docker-compose -f docker-compose-dev.yml up -d cron
```

#### 2. 動作確認

cronログを確認して、監視スクリプトが実行されているか確認します：

```bash
# ログをリアルタイムで監視
docker logs -f cron

# 過去のログを確認
docker logs cron --tail 50
```

#### 3. 手動テスト

コンテナ内でコマンドを手動実行してテストできます：

```bash
docker-compose -f docker-compose-dev.yml exec cron python manage.py check_security_log
docker-compose -f docker-compose-dev.yml exec cron python manage.py check_debug_log
```

---

## 動作確認

1. 管理者アカウントでログイン
2. `security.log` にログが記録されることを確認
3. 即座にメールが送信されることを確認
4. 5分後に定期レポートメールが送信されることを確認

## ログファイル

- **security.log**: セキュリティイベントのログ
- **django_debug.log**: アプリケーションのエラー・警告ログ
- **security_check.log**: セキュリティログ定期チェックの実行ログ
- **debug_check.log**: デバッグログ定期チェックの実行ログ

## メール通知の種類

### 1. セキュリティ・エラーレポート
- **頻度**: 毎日6時（過去24時間に対象があった場合のみ、最大1通）
- **内容**:
  - 管理画面探索、CSRF拒否、ログイン失敗などのカテゴリ別件数
  - 特権ユーザーログイン（詳細）
  - ERROR / CRITICAL（優先して詳細を掲載、詳細全体で最大20件）
  - WARNING、404、通常のbot探索はメール詳細から除外

### 2. 即座の通知（オプション）
- **頻度**: 管理者・スタッフログイン時
- **設定**: `SEND_INSTANT_SECURITY_EMAIL=True` で有効化

## トラブルシューティング

### メールが送信されない場合
1. `secret.env` でメール設定を確認:
   ```
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   ```

2. Gmailの場合、アプリパスワードを使用していることを確認

3. `project/settings.py` のログ設定を確認（上記セットアップ手順参照）

### cronコンテナが動作しない場合
1. cronコンテナの状態を確認:
   ```bash
   docker ps | grep cron
   ```

2. cronコンテナのログを確認:
   ```bash
   docker logs cron --tail 50
   ```

3. cronコンテナ内でcronが実行されているか確認:
   ```bash
   docker exec cron ps aux | grep cron
   ```

4. cron設定ファイルを確認:
   ```bash
   docker exec cron cat /etc/cron.d/recurring-payments
   ```

5. コンテナを再起動:
   ```bash
   docker-compose -f docker-compose-dev.yml restart cron
   ```

### エラーログが記録されない場合
1. `project/settings.py` のLOGGING設定を確認
2. ログファイルの書き込み権限を確認
3. Djangoアプリケーションが正常に動作しているか確認

## メール送信先の変更

`project/settings.py` で送信先を変更できます：

```python
SECURITY_EMAIL_RECIPIENTS = ['recipient1@example.com', 'recipient2@example.com']
```

## 設定の詳細

### project/settings.py の主要設定

```python
# メール設定
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'carbohydratepro@gmail.com'
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# 監視設定
SEND_INSTANT_SECURITY_EMAIL = False  # True: 特権ログインの即座通知あり
SEND_PERIODIC_SECURITY_EMAIL = True  # False: 日次レポートを停止
SECURITY_ALERT_EMAIL = 'carbohydratepro@gmail.com'

# ログ設定
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'security.log',
            'maxBytes': 1024*1024*5,  # 5MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'debug_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'django_debug.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django': {
            'handlers': ['debug_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

## 注意事項

- メール送信には有効なSMTP設定が必要です
- 日次レポートは1日1通を上限とし、通常のWARNINGは件数集計だけに使います
- 本番環境では必ずSSL/TLS接続を使用してください
- 頻繁なメール送信により、メールサーバーの制限に達する可能性があります
