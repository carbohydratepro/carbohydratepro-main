# セキュリティログ監視ガイド

本書は、`security.log`と`django_debug.log`から送信する日次レポートの現行仕様を扱う。
ディスク・Docker・S3を含む運用全体は
[本番運用・容量管理](production-maintenance.md)を参照する。

## 現行方針

旧運用の1分ごとのセキュリティ通知と、5分ごとのWARNING通知は廃止した。
Dockerのcronコンテナが毎日6:00 JSTに過去24時間を集約し、対象がある場合だけ
定期レポートを1通送信する。

```cron
0 6 * * * root cd /code && python manage.py check_security_log --hours 24 >> /var/log/cron.log 2>&1
```

通常運用では`check_debug_log`を定期実行しない。コマンド自体は互換性のため残っているが、
旧5分監視を復活させない。

## 集計対象

### security.log

次のイベントはカテゴリ別件数として集約する。

- 特権ユーザーログイン
- 存在しないユーザーへのログイン試行
- ロック中アカウントへのログイン試行
- 管理画面への未認証アクセス
- CSRF拒否
- その他のアクセス拒否・セキュリティイベント

管理画面探索、CSRF拒否、通常のbotアクセスなどの日常的なノイズは、
メール本文へ1件ずつ掲載しない。特権ユーザーログインだけを要確認の詳細へ載せる。

### django_debug.log

- `ERROR`と`CRITICAL`を件数・詳細の対象にする。
- `WARNING`、404、通常のbot探索は詳細通知の対象外とする。
- 詳細は`SECURITY_REPORT_MAX_DETAILS`件までとし、既定値は20件である。

両ログに対象がなければメールを送信しない。

## 通知設定

設定は環境変数から読み込む。

| 変数 | 既定値 | 用途 |
| --- | --- | --- |
| `SEND_PERIODIC_SECURITY_EMAIL` | `True` | 日次レポートの有効・無効 |
| `SEND_INSTANT_SECURITY_EMAIL` | `False` | 特権ログインの即時通知 |
| `SECURITY_REPORT_MAX_DETAILS` | `20` | メールへ載せる詳細の上限 |
| `SECURITY_ALERT_EMAIL` | アプリ既定値 | 送信先 |

日次レポートは最大1日1通である。
`SEND_INSTANT_SECURITY_EMAIL=True`を明示した場合は、特権ログイン時のメールが別に送信される。

SMTP認証情報は`secret.env`で管理し、ドキュメント、ログ、Gitへ記録しない。

## ログファイル

| ファイル | Djangoハンドラー | ローテーション |
| --- | --- | --- |
| `security.log` | WARNING以上 | 10MB、5世代 |
| `django_debug.log` | INFO以上 | 10MB、5世代 |

現在ログと番号付きローテーションログのうち、指定した24時間に含まれる行を集計する。
ログは別途、毎時S3へ圧縮退避される。

## 動作確認

cronコンテナと設定を確認する。

```bash
docker-compose -f docker-compose-dev.yml ps cron
docker exec cron cat /etc/cron.d/recurring-payments
docker logs cron --tail 100
```

コンテナの`/var/log/cron.log`は標準出力へtailされるため、`docker logs cron`で確認できる。

手動実行する場合、対象イベントがあれば実際にメールを送信する。
送信先とSMTP設定を確認してから実行する。

```bash
docker-compose -f docker-compose-dev.yml exec -T cron \
  python manage.py check_security_log --hours 24
```

## トラブルシューティング

### メールが多い

1. `/etc/cron.d/recurring-payments`が1日1回になっているか確認する。
2. ホスト側cronに`check_security_log`や`check_debug_log`が重複していないか確認する。
3. `SEND_INSTANT_SECURITY_EMAIL`が意図せず有効になっていないか確認する。
4. 同じcronコンテナが複数起動していないか確認する。

### メールが届かない

1. cronコンテナが稼働しているか確認する。
2. `docker logs cron --tail 100`で実行結果を確認する。
3. `SEND_PERIODIC_SECURITY_EMAIL`が有効か確認する。
4. `SECURITY_ALERT_EMAIL`とSMTP設定を確認する。
5. 対象期間にセキュリティイベントまたはERROR／CRITICALが存在するか確認する。

### ログが記録されない

1. gunicornコンテナが正常に稼働しているか確認する。
2. `project/settings/base.py`の`LOGGING`設定を確認する。
3. コンテナから`security.log`と`django_debug.log`へ書き込めるか確認する。

## 関連実装

- cron設定: `crontab`
- 日次コマンド: `auth_app/management/commands/check_security_log.py`
- ログ分類: `auth_app/log_monitoring.py`
- 設定: `project/settings/base.py`
- テスト: `auth_app/tests/test_log_monitoring_commands.py`
