# ログ監視設定ガイド

## 概要
このシステムは以下のログファイルを監視し、問題が検知された場合にメール通知を送信します：

1. **security.log**: セキュリティイベント（管理者ログイン、不正アクセス試行など）- **1分ごと**に監視
2. **django_debug.log**: アプリケーションエラー（ERROR、WARNING、CRITICAL、Traceback）- **5分ごと**に監視

## 本番環境・ローカル環境（Docker環境）

**重要**: 現在、監視スクリプトはDockerのcronコンテナで自動実行されます。

### 自動実行の仕組み

監視スクリプトは定期支払い機能と同じcronコンテナで実行されます：
- `crontab` ファイルに設定が記載されています
- コンテナ起動時に自動的に監視が開始されます
- 手動設定は不要です

## 機能
1. **リアルタイム通知**: 管理者・スタッフがログインした際に即座にメール送信（オプション）
2. **定期セキュリティ監視**: 1分ごとにsecurity.logを確認し、過去1分間の活動をレポート
3. **定期エラー監視**: 5分ごとにdjango_debug.logを確認し、エラー・警告・Tracebackをレポート

## セットアップ方法

### Docker環境（本番・ローカル共通）

監視機能は既にcronコンテナに統合されています。以下の手順で有効化できます：

#### 1. コンテナの再起動

監視機能を有効化するには、cronコンテナを再起動してください：

```bash
# 本番環境
docker-compose build cron
docker-compose up -d cron

# ローカル環境
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
# 本番環境
docker-compose exec cron python manage.py check_security_log
docker-compose exec cron python manage.py check_debug_log

# ローカル環境
docker-compose -f docker-compose-dev.yml exec cron python manage.py check_security_log
docker-compose -f docker-compose-dev.yml exec cron python manage.py check_debug_log
```

---

## レガシー環境（非Docker）

以下の方法は、Docker環境を使用しない場合のみ参照してください。

### Linux/WSL環境（cron）- 非推奨

**注意**: Docker環境を使用している場合、この方法は不要です。

#### 手順:

1. スクリプトに実行権限を付与:
```bash
chmod +x /home/carbohydratepro-main/check_security_only.sh
chmod +x /home/carbohydratepro-main/check_debug_only.sh
```

2. crontabを編集:
```bash
crontab -e
```

3. 以下の行を追加:
```
# セキュリティログ監視（1分ごと）
* * * * * /home/carbohydratepro-main/check_security_only.sh

# デバッグログ監視（5分ごと）
*/5 * * * * /home/carbohydratepro-main/check_debug_only.sh
```

4. crontabを保存して終了

5. cronが正しく動作しているか確認:
```bash
crontab -l
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

### 1. セキュリティレポート
- **頻度**: 1分ごと（過去1分間にイベントがあった場合のみ）
- **内容**:
  - 特権ユーザーログイン
  - 警告 (WARNING)
  - エラー (ERROR)
  - その他のセキュリティイベント

### 2. エラーレポート
- **頻度**: 5分ごと（過去5分間にエラーがあった場合のみ）
- **内容**:
  - CRITICAL: 重大なエラー
  - ERROR: アプリケーションエラー
  - WARNING: 警告
  - Traceback: スタックトレース

### 3. 即座の通知（オプション）
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
   # ローカル環境
   docker-compose -f docker-compose-dev.yml restart cron

   # 本番環境
   docker-compose restart cron
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
SEND_INSTANT_SECURITY_EMAIL = False  # True: 即座通知あり、False: 定期レポートのみ
SECURITY_EMAIL_RECIPIENTS = ['carbohydratepro@gmail.com']

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
- セキュリティログは1分間隔、デバッグログは5分間隔で監視されます
- Tracebackも自動的にエラーとしてカウントされます
- 本番環境では必ずSSL/TLS接続を使用してください
- 頻繁なメール送信により、メールサーバーの制限に達する可能性があります
