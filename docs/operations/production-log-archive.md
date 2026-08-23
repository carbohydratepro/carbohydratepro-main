# 本番ログのS3アーカイブ

本番運用全体の入口は[本番運用・容量管理](production-maintenance.md)を参照する。
本書はログアーカイブ固有の保存・権限・復旧条件を扱う。

## 保存先と機密性

- バケット: `s3://carbohydratepro-system-logs/production/`
- リージョン: `ap-northeast-1`
- パブリックアクセスはすべてブロックし、TLSとSSE-S3（AES256）を必須にする。
- system journalとアプリログには、IPアドレス、入力メールアドレス、User-Agent、URL、エラー詳細が含まれる可能性がある。
- S3側の自動削除・ライフサイクルルールは設定しない。

## 転送と削除の順序

1. 初回は現在参照できるsystem journal全体を圧縮して退避する。
2. 以後は完了した1時間ごとのsystem journalと、アプリログの時間スナップショットを退避する。
3. S3のオブジェクト容量、SHA-256メタデータ、AES256暗号化を照合する。
4. ローテーション済みアプリログは、転送中に変更されていない場合だけローカルから削除する。
5. すべて成功した場合だけ、system journalのアーカイブ済みファイルを7日・1GB以内へ整理する。
6. 失敗時はローカルログを削除せず、既存の日次セキュリティレポートへ最大1日1回だけ失敗を記録する。

## 保存形式と復元範囲

- system journalは`journalctl --output=short-iso`のテキスト出力をgzip圧縮する。
- ログ本文と時刻の調査を目的とし、元の`.journal`バイナリや全構造化フィールドの完全復元は対象外とする。
- アプリログは現在ログの時間スナップショットと、番号付きローテーションログをgzip圧縮する。
- S3側の自動削除はないため、保存期間は無期限である。削除方針を追加する場合は別途承認を得る。

## 運用パス

- 実行スクリプト: `scripts/archive-production-logs.sh`
- cron: `/etc/cron.d/carbohydratepro-log-archive`（毎時10分）
- 実行ログ: `/var/log/carbohydratepro-log-archive.log`
- 設定: `/etc/carbohydratepro/log-archive.env`（root所有・`0600`）
- 進捗: `/var/lib/carbohydratepro-log-archive/`
- 運用ログのlogrotate: `/etc/logrotate.d/carbohydratepro-maintenance`

## 認証情報

- IAMユーザー `carbohydratepro-system-log-uploader` をログ転送専用とする。
- 権限は `production/*` への `s3:PutObject`、失敗した分割アップロードを中止する `s3:AbortMultipartUpload`、検証用の `s3:GetObject` のみに限定し、完成オブジェクトの削除・一覧権限は付与しない。
- アクセスキーは `/etc/carbohydratepro/log-archive.env` にroot所有・`0600`で保存し、リポジトリには保存しない。
- 定期的にアクセスキーの最終使用日時を確認し、必要に応じてローテーションする。

## 初回運用結果（2026-08-23）

- 172オブジェクト、合計33,835,782バイトをS3で確認した。
- 初回journal全量1件、時間別journal 168件、アプリログ3件を保存した。
- 初回journalオブジェクトは27,218,181バイトで、AES256暗号化とSHA-256メタデータを確認した。
- S3検証後、system journalは4.0GBから72MBへ減少した。
- S3ライフサイクルは未設定である。
