# ログ監視設定ガイド

## 概要
このシステムは以下のログファイルを監視し、問題が検知された場合にメール通知を送信します：

1. **security.log**: セキュリティイベント（管理者ログイン、不正アクセス試行など）- **1分ごと**に監視
2. **django_debug.log**: アプリケーションエラー（ERROR、WARNING、CRITICAL、Traceback）- **5分ごと**に監視

## 機能
1. **リアルタイム通知**: 管理者・スタッフがログインした際に即座にメール送信（オプション）
2. **定期セキュリティ監視**: 1分ごとにsecurity.logを確認し、過去1分間の活動をレポート
3. **定期エラー監視**: 5分ごとにdjango_debug.logを確認し、エラー・警告・Tracebackをレポート

## セットアップ方法

### 1. コマンドのテスト
まず、管理コマンドが正しく動作するか確認します：

```bash
# セキュリティログチェック
python manage.py check_security_log

# デバッグログチェック
python manage.py check_debug_log
```

### 2. Windows環境（タスクスケジューラ）

#### セキュリティログ監視タスク（1分ごと）:

1. タスクスケジューラを開く
   - Win + R → `taskschd.msc` → Enter

2. 「タスクの作成」をクリック

3. **全般タブ**:
   - 名前: `セキュリティログ監視（1分）`
   - 説明: `1分ごとにセキュリティログを確認してメール通知`
   - 「最上位の特権で実行する」にチェック

4. **トリガータブ**:
   - 「新規」をクリック
   - 繰り返し間隔: `1分間`
   - 継続時間: `無期限`
   - 有効: チェック

5. **操作タブ**:
   - 「新規」をクリック
   - プログラム/スクリプト: `\\wsl.localhost\archlinux\home\carbohydratepro-main\check_security_only.bat`
   - 開始: `\\wsl.localhost\archlinux\home\carbohydratepro-main`

6. **条件タブ**:
   - 「コンピューターをAC電源で使用している場合のみタスクを開始する」のチェックを外す

7. 「OK」をクリックして保存

#### デバッグログ監視タスク（5分ごと）:

1. タスクスケジューラで「タスクの作成」をクリック

2. **全般タブ**:
   - 名前: `デバッグログ監視（5分）`
   - 説明: `5分ごとにデバッグログを確認してメール通知`
   - 「最上位の特権で実行する」にチェック

3. **トリガータブ**:
   - 「新規」をクリック
   - 繰り返し間隔: `5分間`
   - 継続時間: `無期限`
   - 有効: チェック

4. **操作タブ**:
   - 「新規」をクリック
   - プログラム/スクリプト: `\\wsl.localhost\archlinux\home\carbohydratepro-main\check_debug_only.bat`
   - 開始: `\\wsl.localhost\archlinux\home\carbohydratepro-main`

5. **条件タブ**:
   - 「コンピューターをAC電源で使用している場合のみタスクを開始する」のチェックを外す

6. 「OK」をクリックして保存

### 3. Linux/WSL環境（cron）

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

### 4. 動作確認

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

### タスクが実行されない場合（Windows）
1. タスクスケジューラで「タスクの実行」を手動でテスト
2. `security_check.log` と `debug_check.log` でエラーを確認
3. Pythonのパスが正しいか確認
4. check_security.bat のパスが正しいか確認

### cronが動作しない場合（Linux）
1. cronサービスが実行中か確認:
   ```bash
   sudo systemctl status cron
   ```

2. ログを確認:
   ```bash
   grep CRON /var/log/syslog
   ```

3. スクリプトの実行権限を確認:
   ```bash
   ls -l /home/carbohydratepro-main/check_security.sh
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
