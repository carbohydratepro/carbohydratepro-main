# 本番ログのS3アーカイブ

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

## 認証情報

- IAMユーザー `carbohydratepro-system-log-uploader` をログ転送専用とする。
- 権限は `production/*` への `s3:PutObject`、失敗した分割アップロードを中止する `s3:AbortMultipartUpload`、検証用の `s3:GetObject` のみに限定し、完成オブジェクトの削除・一覧権限は付与しない。
- アクセスキーは `/etc/carbohydratepro/log-archive.env` にroot所有・`0600`で保存し、リポジトリには保存しない。
- 定期的にアクセスキーの最終使用日時を確認し、必要に応じてローテーションする。
