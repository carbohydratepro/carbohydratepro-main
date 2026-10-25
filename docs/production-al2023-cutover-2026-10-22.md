# AL2023への本番切り替え・復旧手順

状態: ユーザーの最終承認後、2026-10-22に本番切り替えと実ログ保存を実施済み。以下は実施順序・復旧手順の記録であり、古いdumpを本番へ再適用しない。

2026-10-25追記: 本番は追加3コミット反映後の `917b40b`。セキュリティ関連10ファイルのローカルとのSHA256一致、4サービス・公開ログイン・定期処理の正常を再確認した。詳細は `production-security-hardening-2026-10-22.md`。以下の `8b294bd` は移行当時の基準であり、現在の本番へ戻す指示ではない。

## 旧サーバー削除（2026-10-24 JST）

ユーザーの明示依頼で `docker-django-app-carbohydratepro` を削除し、AWSの `DeleteInstance` が `Succeeded` / terminalとなったことと一覧からの消失を確認した。固定IP `54.238.169.177` は新本番に接続されたまま、4サービス稼働と公開ログインHTTP 200を再確認した。旧インスタンスへの切り戻しはできない。以下の旧サーバーを使う手順は移行当時の履歴であり、現在の復旧には使用しない。

削除前に移行時の `final-database.dump` / `final-runtime.tar.gz` のSHA256一致を確認し、新本番の最新DBとアプリ設定・media・static等を `workspace/security-hardening-20261022/pre-legacy-delete-20261023T191339Z/` に保存した。所有者限定権限で保持し、dumpの目次読み取り・gzip検査とSHA256記録を実施。今回の最新dumpについて復元テストは未実施。稼働中の個別取得なのでDBとファイルを同時点に固定したバックアップではない。DBの定期バックアップを新設したものではない。

削除操作ID: `971077b1-2dda-48b8-8ffa-687a18617896`。DNS・固定IP・CloudFront・S3・IAMは削除対象に含めていない。

## 移行時の実施結果

- 固定IP `54.238.169.177` は新AL2023へ移動済み。旧AL2の移行直後のIPは `57.180.48.3`（削除済みのため接続しない）。新本番のSSHは `workspace/security-hardening-20261022/migration-ssh-config` の検証済み鍵を使う。
- 旧側で更新停止後に取得した最終dumpは40テーブルの件数・内容ハッシュが一致。設定・media・静的ファイル438件の内容も一致した。
- 旧側のメンテナンス開始は2026-10-22 14:29:58 UTC頃、新側の利用再開は14:37:22 UTC（JSTでは23:37:22）。旧gunicorn・cronは停止したまま、新側の4サービスが稼働。
- 利用再開後、展開時のumaskによりstatic_rootが0700/0600となりCSSが403になる不具合を発見した。元アーカイブのモードへ復元し、14:44:37 UTCに公開CSSの200を確認。CSS/JS計5件のCloudFrontキャッシュミス200と元データのハッシュ一致を検証した。秘密設定は0600を維持。
- CloudFrontは `Deployed`、HTTPS 443のみ・TLS1.2・秘密ヘッダーをAPIで再照合。443/8000/5432への一般接続元からの直接接続は遮断。公開ログイン・デモ4画面と静的配信が正常。
- 実クライアントIPのアクセスログ記録、秘密値がログに出ないこと、証明書/IP同期timer、実ログのS3保存・暗号化・容量/ハッシュ照合を確認。
- 移行時の復旧用旧設定は旧サーバー `/home/ec2-user/al2023-cutover-backup-RU4ubN2J/` に保持していた。旧サーバー削除後はこのパスも利用できない。

## 対象と実行条件

- 旧: `docker-django-app-carbohydratepro`、Amazon Linux 2。
- 新: `carbohydratepro-al2023-20261022`、Amazon Linux 2023。
- 固定IP: `app-carbohydratepro` / `54.238.169.177`。切り替え前は旧側、現在は新側に接続。
- CloudFront: `E14S8Q3N5USH59`、オリジン `lightsail.carbohydratepro.com`。
- コード: `main` / `8b294bdc156f9965d6ef4ddb8b58ee150778844a` と今回のセキュリティ設定のみ。ローカルの未完了UI変更は含めない。
- 検証証跡・一時設定: `workspace/security-hardening-20261022/`、所有者のみアクセス可能、Git対象外。
- 実行前に旧側のHEAD・差分、両サーバーの稼働状態、最新のCloudFront設定・ETagとファイアウォールを再取得する。想定外の変更は上書きしない。
- 利用停止は目安10〜20分だが、CloudFrontの反映時間等で延びる可能性がある。完了を確認するまで書き込みとcronを再開しない。

## 承認後の順序

1. 新側のIP範囲更新timerを一時停止する。移行中の8000追加を自動更新に消させない。
2. 旧側のCompose・Nginx設定を別ディレクトリへ保存する。準備した `nginx-maintenance.conf` を旧Nginxの既存bind先へ書き込み、`nginx -t` 後reload。HTTP 503を確認する。
3. **旧側だけ** `docker-compose -f docker-compose-dev.yml stop gunicorn cron`。DBは維持し、未完了のWeb書き込みが終了したことを確認する。
4. 旧側から新しい `pg_dump -Fc`、`secret.env`、media、static_rootを非公開作業領域へ退避する。dump後に `database-manifest.sql` で全テーブルの件数・内容ハッシュを取得し、ファイルSHA256も保存する。
5. **新側だけ** アプリを停止してDBを最終dumpへ復元する。新側の `.env` にあるTLS・再起動設定は旧側の `.env` で上書きしない。既存の検証用media/static_rootを退避したうえで最新を配置する。DB内容・ファイルハッシュ・migration状態を再照合する。
6. 新側の検証用Composeを外し、通常のDockerネットワーク・`project.settings.production` に切り替える。`nginx-transition.conf` と `transition-compose.yml` を使って443/8000を準備する。`/etc/carbohydratepro/maintenance/active` を、workerが読める専用ディレクトリ経由で `/etc/nginx/maintenance/active` に読取専用マウントし、両経路を503にする。DB・gunicorn・Nginxだけを起動し、cronはまだ起動しない。
7. 新側の443はCloudFront範囲への制限を維持する。移行中の8000はNginx内の接続元検証とメンテナンス応答を必須とし、Lightsailルール上限を超えない一時ルールを使う。8000/443両方へ全CIDRを重複登録しない。
8. 固定IPを旧側から切り離して新側へ接続する（下記）。AWS APIで両サーバーの現在のIPを再取得し、`migration-ssh-config` のHostNameだけを更新する。`HostKeyAlias` と照合済み鍵は変えない。IPが入れ替わるため古いSSH設定を使い続けない。
9. CloudFrontの最新設定とETagを再取得する。対象オリジンだけを `https-only`、HTTPS 443、`OriginSslProtocols=[TLSv1.2]` へ変更し、新側の既存 `origin-token` を `X-Carbohydratepro-Origin` に設定する。秘密値を表示せず0600のJSON経由で更新する。ほかのキャッシュ設定等は保持する。
10. Distributionが `Deployed` になるまで待ち、新側アクセスログでCloudFrontからHTTPSへ到達していることを確認。メンテナンス中なのでHTTP 503が正常。アプリは管理接続からUnixソケットで参照確認し、静的ファイルのハッシュも照合する。公開経路のメンテナンスを外して検証しない。
11. 新側を最終 `nginx/production.conf` と443のみのComposeへ切り替え、8000のマッピング・ファイアウォール許可を削除する。公開HTTPSのキャッシュミスでログイン・デモ・静的ファイル200を確認する。この段階が新側での利用・書き込み再開となる。
12. 新側だけcronを起動する。旧側のgunicorn・cronが停止したままであることを照合。IP範囲更新を1回実行してtimerを再開し、証明書timerも有効であることを確認する。
13. 実ログ保存の承認を受けた場合、新側の既存ログアーカイブスクリプトと毎時cronを有効にする。S3保存先は `s3://carbohydratepro-system-logs/production/carbohydratepro-al2023-20261022/`。容量・SHA256・AES256暗号化の照合成功を確認する。
14. 旧サーバーは削除せず、停止したアプリとDBを復旧用に保持する。利用再開後の監視結果を報告し、旧サーバー削除とローカルの秘密情報入り一時バックアップの整理は別途判断する。

実施した固定IP操作（再実行しない）:

```bash
aws lightsail detach-static-ip --static-ip-name app-carbohydratepro --region ap-northeast-1
aws lightsail attach-static-ip --static-ip-name app-carbohydratepro \
  --instance-name carbohydratepro-al2023-20261022 --region ap-northeast-1
```

CloudFront操作は、実行直前のETagと秘密値を含む非公開JSONを使う:

```bash
aws cloudfront update-distribution --id E14S8Q3N5USH59 \
  --if-match "$current_etag" \
  --distribution-config file://workspace/security-hardening-20261022/cloudfront-cutover.json
```

実際のコマンドでは応答も非公開ファイルへリダイレクトし、カスタムヘッダーを端末へ表示しない。

## 復旧条件

- 利用再開前に失敗した場合、旧DBに新しい書き込みは発生していない。CloudFrontを保存したHTTP 8000設定へ戻し、固定IPを旧側へ付け戻し、旧Nginx設定を復元して旧gunicorn・cronを再開できる。新側はメンテナンス状態を維持する。失敗段階を報告してから復旧する。
- **新側で利用を再開した後は、IPだけを戻さない。** 両側の書き込みを止め、新側DBとmediaの最新状態を保全してから旧側へのデータ反映が必要か判断する。旧コピーへの単純切り戻しは、新しいデータを失う。
- 固定IPのdetach後にattachが失敗した場合、IPを解放・削除しない。元の旧インスタンスへ再attachできる状態を保持する。
- 旧サーバーを停止してもインスタンス料金は続く。追加費用がなくなるのは旧サーバーの削除後である。固定IPの移し替えは[既存IPを新インスタンスへ引き継ぐAWS手順](https://repost.aws/knowledge-center/lightsail-fresh-install-of-instance)に従う。
