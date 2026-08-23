# 本番運用・容量管理

本書は、CarbohydratePro本番環境のディスク容量、Docker資産、ログのS3退避、
セキュリティ通知を確認するための入口である。実装の詳細は次の資料を参照する。

- [本番ログのS3アーカイブ](production-log-archive.md)
- [セキュリティログ監視](security-monitoring.md)
- [S3バケットポリシー](s3-log-bucket-policy.json)
- [ログ転送用IAMポリシー](s3-log-uploader-policy.json)

## 現在の運用構成

| 対象 | 実行時刻 | 処理 | 設定場所 |
| --- | --- | --- | --- |
| Docker整理 | デプロイ前、および毎週日曜4:30 JST | 7日より古い未使用イメージとBuildKitキャッシュを削除 | `/etc/cron.d/carbohydratepro-docker-maintenance` |
| S3ログ退避 | 毎時10分 | 完了した時間のjournalとアプリログを圧縮・転送・検証 | `/etc/cron.d/carbohydratepro-log-archive` |
| セキュリティレポート | 毎日6:00 JST | 過去24時間を集約し、対象がある場合だけ1通送信 | cronコンテナの`/etc/cron.d/recurring-payments` |
| 運用ログ整理 | 毎週 | Docker整理・S3退避の実行ログを8世代圧縮保持 | `/etc/logrotate.d/carbohydratepro-maintenance` |

本番でも`docker-compose-dev.yml`を使用する構成は意図されたものである。

## 2026-08-23時点の本番確認結果

この値は導入直後のスナップショットであり、継続的な上限値ではない。

| 確認項目 | 結果 |
| --- | --- |
| 本番コミット | `33fc3fe` |
| ルートディスク | 40GB中9.4GB使用、31GB空き、使用率24% |
| system journal | 4.0GBから72MBへ削減 |
| S3保存 | 172オブジェクト、33,835,782バイト |
| S3内訳 | 初回全量1件、時間別journal 168件、アプリログ3件 |
| 初回journalオブジェクト | 27,218,181バイト、SSE-S3（AES256）、SHA-256メタデータ確認済み |
| Docker | 6イメージ中4イメージ稼働、4コンテナ稼働 |
| アプリケーション | HTTP 200を確認 |
| S3ライフサイクル | 未設定（自動削除なし） |

## ディスク不足の原因と対策

### 原因

2026-08-12の調査では、40GBディスクの使用率が98%まで上昇していた。
主因はアプリケーションの稼働イメージ自体ではなく、過去のDockerビルドで残った
未使用イメージとBuildKitキャッシュだった。system journalも約4GBを使用していた。

### 対策

- デプロイ前に7日より古い未使用Docker資産を整理する。
- 同じ処理を週次cronでも実行し、デプロイ間隔が空いても蓄積を防ぐ。
- 稼働中・停止中のコンテナが参照しているイメージとボリュームは削除しない。
- 7日以内の未使用資産はロールバック余地として保持するため、整理直後も
  `docker system df`の`RECLAIMABLE`が0になるとは限らない。
- system journalとアプリログをS3へ退避し、検証後にローカルを整理する。

実装は`run-production-deploy.sh`と
`scripts/install-production-docker-maintenance.sh`を参照する。

## ログの保存と削除

ログは次の順序で処理する。

1. 初回は参照可能なsystem journal全体をテキストへ書き出してgzip圧縮する。
2. 以後は完了した1時間ごとのjournalと、現在のアプリログをS3へ転送する。
3. S3の容量、SHA-256メタデータ、AES256暗号化を照合する。
4. ローテーション済みアプリログは、転送中に変更されていない場合だけ削除する。
5. すべて成功した場合だけ、journalのアーカイブ済みファイルを7日・1GB以内へ整理する。

途中で失敗した場合は進捗地点を保持し、ローテーション済みログの削除とjournal整理を
実行しない。次回は確認済みの時間の次から再開する。

### 保存範囲の注意

system journalは`journalctl --output=short-iso`のテキストとして保存する。
表示されるログ本文と時刻は保持されるが、元の`.journal`バイナリそのものや、
この出力形式に含まれない構造化フィールドを復元する用途ではない。
バイナリ完全保存が必要な監査要件が生じた場合は、別方式を設計する。

S3側には自動削除を設定していないため、S3上のログは手動で削除しない限り残る。
保存量と費用は定期的に確認する。

## S3と認証情報

- バケットは通常のAmazon S3 `carbohydratepro-system-logs`（東京リージョン）を使う。
- パブリックアクセスをすべてブロックし、TLSとSSE-S3（AES256）を必須とする。
- 専用IAMユーザー`carbohydratepro-system-log-uploader`には、
  `production/*`への転送・転送検証・失敗した分割アップロードの中止だけを許可する。
- 一覧権限と完成オブジェクトの削除権限は付与しない。
- アクセスキーは本番の`/etc/carbohydratepro/log-archive.env`へ
  root所有・`0600`で保存し、リポジトリや運用ログには出力しない。

## セキュリティレポート

旧運用の1分ごとの`security.log`監視と5分ごとの`django_debug.log`監視は廃止した。
現在は毎日6:00 JSTに過去24時間を集約する。

- 管理画面探索、CSRF拒否、ログイン失敗などはカテゴリ別件数だけを載せる。
- 特権ユーザーログインとERROR／CRITICALだけを詳細に載せる。
- 詳細は既定で最大20件とする。
- 対象イベントがない場合はメールを送信しない。
- 定期レポートは最大1日1通である。即時通知を明示的に有効化した場合は別途送信される。
- 送信履歴はDBへJST日付単位で保存し、cronが誤って頻回実行されても同日の重複送信を拒否する。

## 読み取り確認

本番ホストでは、次のコマンドで機密情報を表示せずに状態を確認できる。

```bash
df -h /
sudo journalctl --disk-usage
docker system df
docker-compose -f docker-compose-dev.yml ps
sudo cat /etc/cron.d/carbohydratepro-docker-maintenance
sudo cat /etc/cron.d/carbohydratepro-log-archive
docker exec cron cat /etc/cron.d/recurring-payments
sudo tail -n 100 /var/log/carbohydratepro-log-archive.log
sudo tail -n 100 /var/log/carbohydratepro-docker-maintenance.log
```

`/etc/carbohydratepro/log-archive.env`の内容は表示しない。所有者と権限だけを確認する。

```bash
sudo stat -c '%U:%G %a %n' /etc/carbohydratepro/log-archive.env
```

S3管理権限を持つ端末では、保存件数とライフサイクル設定を確認できる。

```bash
aws s3api list-objects-v2 \
  --bucket carbohydratepro-system-logs \
  --prefix production/docker-django-app-carbohydratepro/ \
  --region ap-northeast-1 \
  --query '[length(Contents),sum(Contents[].Size)]'

aws s3api get-bucket-lifecycle-configuration \
  --bucket carbohydratepro-system-logs \
  --region ap-northeast-1
```

後者が`NoSuchLifecycleConfiguration`を返すことが、現在の「自動削除なし」の状態である。

## 障害時の対応

### S3ログ退避に失敗した場合

1. `/var/log/carbohydratepro-log-archive.log`で失敗箇所を確認する。
2. ディスクに緊急性がなければ、S3確認前にjournalやローテーションログを削除しない。
3. S3権限、ネットワーク、設定ファイルの所有者・権限を確認する。
4. 原因を修正後、`sudo scripts/archive-production-logs.sh`を再実行する。
5. journal容量、S3件数、状態ファイルの進捗を再確認する。

状態は`/var/lib/carbohydratepro-log-archive/`へ保存される。
設定ファイルや状態ファイルを手作業で削除すると、重複転送や未転送期間が生じるため、
復旧目的でも根拠なく削除しない。

### ディスク使用率が再上昇した場合

1. `df -h /`、`docker system df`、`sudo journalctl --disk-usage`で内訳を確認する。
2. 稼働コンテナとHTTP応答を確認する。
3. 自動処理の実行ログとcronサービスを確認する。
4. 削除前に、対象が未使用資産またはS3検証済みログであることを確認する。

使用率80%を超えた場合は原因を調査し、90%を超える前に対処する。

## 関連コミット

- `2c21239`: 本番のDocker保守とセキュリティ通知を改善
- `1fe7f1d`: Dockerの週次保守を追加
- `6873860`: 本番ログのS3アーカイブを追加
- `33fc3fe`: 本番journalの時刻指定をAmazon Linux 2互換形式へ修正
