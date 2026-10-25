# 本番セキュリティ対策の実施状況と移行手順

更新日: 2026-10-25。元の点検結果は `production-security-check-2026-10-22.md`。

**最終状態:** ユーザーの最終承認後、本番をAL2023へ移行し、HTTPS・秘密ヘッダー・実ログの毎時S3保存を有効化済み。新本番は `carbohydratepro-al2023-20261022` / `54.238.169.177`。旧サーバーは2026-10-24 JSTにユーザーの明示依頼で削除済み。削除前に新本番の最新DB・runtimeを非公開領域へ保存した。切り替え中に発生した静的ファイル権限の不具合も修正し、公開配信を再検証済み。詳細は `production-al2023-cutover-2026-10-22.md`。

## Git状態の統一完了（2026-10-25）

ユーザーの明示依頼により `3c1e8f9` / `9f3ad56` をorigin/mainへpushし、本番を `917b40b` から `9f3ad56` へfast-forwardした。先行適用済み差分12ファイルの内容・実行権限を対象コミットと照合し、`/home/ec2-user/git-unification-backup-35bvwecq/` にファイル・Git index・差分を保全してから、一致するパスだけをstageして統合した。本番の未コミット・未追跡差分は解消済み。

稼働設定の内容・inode、秘密設定、4コンテナIDは前後で不変。Nginx構文・Django check、公開ログインHTTP 200、CSS/JS3件の配信SHA256一致、証明書/IP同期timerと毎時ログ保存の正常を確認した。コンテナ再構築・再起動・DB変更は行っていない。本節を含む完了記録は文書のみの後続コミットとして同じmainへ反映する。

## 統一前の追加デプロイ照合（2026-10-25）

- 本番・ローカルのコミットとGitHubのmainは `917b40b`。移行後に `7c80b55`（問い合わせ通知日時）、`fd5a1e8`（本番外観を維持した操作改善）、`917b40b`（方針・検証記録）が反映されている。
- 本番のCompose・デプロイスクリプト・Nginx設定・運用スクリプト3件・systemd定義4件、計10ファイルのSHA256がローカルのコミット対象と一致。4コンテナ稼働、公開ログインHTTP 200、証明書/IP範囲更新の成功とtimer有効、毎時ログ保存の正常終了を再確認した。
- ローカルの既存テストはファイアウォール4件、隔離DockerでのTLS・アクセス制限等3件が成功。シェル構文検査も成功。
- 本コミットは既に本番へ適用されたセキュリティ差分を履歴へ取り込むもの。本番は読み取り確認のみで、push・追加デプロイは行わない。本番側には同内容の変更・未追跡ファイルが残るため、次回反映時はバックアップと内容照合のうえGitの追跡状態を整合させる。単純なpullが未コミット変更・未追跡ファイルで停止する可能性がある。

以下の適用・移行手順は10月22日時点の実施履歴。

## 適用済み

### 接続元制限

- 本番LightsailのTCP 22を、現在の管理元IPv4 `/32` と `lightsail-connect` に限定。IPv6の全世界向けSSH許可を削除した。
- TCP 8000をAWS公式 `CLOUDFRONT_ORIGIN_FACING` の範囲だけに限定した。取得元の `createDate` は `2026-10-22-01-37-05`。
- 元データはIPv4 49範囲、IPv6 38範囲。同じ許可範囲を変えずに隣接CIDRを集約し、他ポートを含む明示ルールはIPv4 52、IPv6 40になった。Lightsailの各60ルール上限内。
- SSHの新規接続成功、CloudFrontのキャッシュミスでログイン画面HTTP 200、一般接続元からの本番8000への接続タイムアウトを確認。
- AWS APIから設定を再取得し、IPv4/IPv6とも計画と完全一致することを検証した。
- 設定の復旧用JSON・適用後JSONは `workspace/security-hardening-20261022/` に保存。git管理外、ディレクトリ0700。管理IPが変わった場合はAWSコンソールで22番の許可IPを更新する。ブラウザSSHの許可は残したが、ブラウザ内での実接続は今回実施していない。
- 80/443/587/ICMP等の既存ルールはこの段階では維持した。8000への許可は自分以外のCloudFrontも含むため、Distribution固有の制限は後述の追加対策が必要。

### Nginx更新

- ユーザーの実行直前承認後、2026-10-22 12:51 JST頃に本番Nginxを1.17.7から1.30.6へ更新。
- 固定イメージ: `nginx:1.30.6@sha256:a7675fcee220f59b4a99f7098c06a0d5d999c2c0ee37c0211efb780536e5cb20`。
- `scripts/update-production-nginx.sh --check` で本番の現行コミット・追跡差分・イメージ・構文を検証し、承認後に `--apply` を実行した。
- 対象リリースは `main` / `8b294bdc156f9965d6ef4ddb8b58ee150778844a`。本番の変更は `docker-compose-dev.yml` のNginxイメージ行のみ。
- 復旧用Composeは `/home/ec2-user/nginx-update-backup-a2p8XWyJ/docker-compose-dev.yml`。旧イメージを削除していない。
- `docker-compose -f docker-compose-dev.yml up -d --no-deps --no-build nginx` でNginxだけ再作成した。アプリ・DB・cronのコンテナIDが更新前後で同一であることを照合。
- 本番内のトップ・ログイン・CSS・JS配信、Nginx構文、CloudFrontのキャッシュミスによるHTTP 200と `nginx/1.30.6` を確認。
- 本番にはイメージ行の未コミット変更が残る。ローカルのUI変更は反映していない。次回の通常デプロイ前に、この限定差分を取り込む必要がある。コミット・pushは今回実行していない。

## 本番適用済み: HTTPS・秘密ヘッダー・接続元ログ

準備したファイル:

- `nginx/production.conf`: HTTPS専用。実際の接続相手がCloudFrontであることと、`X-Carbohydratepro-Origin` の秘密値を両方検証する。
- `scripts/prepare-origin-security.py`: AWS公式IP範囲のJSONから、信頼するプロキシと接続許可範囲を生成する。秘密値は256bit乱数で、既存値があれば再利用する。秘密値を標準出力へ出さず、ファイル0600・ディレクトリ0700で保存する。
- `docker-compose-dev.yml`: Nginxの設定・公開ポート・証明書・秘密設定ディレクトリを環境変数で選べる。既定値では従来どおりHTTP 8000を使う。
- `scripts/tests/test-origin-security.py`: 外部通信できない隔離Dockerネットワークで実際のNginxを起動して検証する。

検証結果: 3テスト成功。正常なTLS証明書検証、秘密値なし/不正値の403、正しい秘密値を持つ非CloudFront接続元の403、任意に付加されたIP・プロトコルの除去、実クライアントIPの記録、秘密ヘッダーをアプリやアクセスログへ渡さないこと、静的資産の配信とキャッシュを確認した。
起動時に必要な設定・証明書がなければ失敗する構成で、制限なしへフォールバックしない。自己署名証明書は隔離テスト専用で、本番には使用しない。

本番の最終構成で使用するCompose変数:

```dotenv
NGINX_PORT=443
NGINX_CONFIG_FILE=./nginx/production.conf
NGINX_SECURITY_DIR=/etc/carbohydratepro/nginx
NGINX_CERTIFICATE_DIR=/etc/letsencrypt
```

有効化の計画（実際の切り替えは別紙の固定IP移行手順で完了済み）:

1. Route 53のDNS-01認証で、`lightsail.carbohydratepro.com` と `carbohydratepro.com` を含む証明書を用意する。Hostヘッダー転送の有無を確認し、CloudFrontの証明書検証に合うSANとする。証明書の配置先名は `live/lightsail.carbohydratepro.com/` に統一する。
2. 自動更新用のDNS権限は対象の検証用TXTレコードだけへ絞る。個人のAWS管理者キーや既存ログアップロード用キーを流用してサーバーへ配らない。更新後の `nginx -t` とreload、更新失敗の検知まで用意してからHTTPSを本番の必須経路にする。
3. 最新のAWS公式IP JSONから秘密設定を生成し、root専用ディレクトリへ配置する。秘密値はCloudFrontのオリジンカスタムヘッダーへ設定し、コンソール出力・Git・通常ログへ残さない。
4. 切り替え中は既存HTTP 8000と新HTTPS 443を両方提供する一時設定を用意し、CloudFrontの設定変更が全エッジへ反映されるまで旧経路を残す。最終用 `production.conf` だけを先に置き換えると旧経路が止まるため、そのまま先行適用しない。
5. CloudFrontのオリジンをHTTPSのみ・443・TLS 1.2へ変更する。現在のOriginSslProtocolsにはSSLv3/TLS1/TLS1.1も登録されているので同時に取り除く。
6. Distributionの反映完了とキャッシュミスでのHTTP 200を確認した後に、8000の公開許可を削除し、443をCloudFront範囲へ限定する。8000と443の両方へ全範囲を登録するとLightsailのルール数上限を超え得るため、移行中の443ではNginx内部の接続元検証も使う。
7. 最終Compose変数へ切り替え、8000の公開マッピングと一時HTTPサーバー設定を外す。次回デプロイのヘルスチェックもHTTPS経由へ変更する。現行デプロイスクリプトは `localhost:8000` を検査するので、修正前に最終構成へ移さない。
8. 通常のログイン記録がCloudFront IPではなく実クライアントIPになることを確認する。過去のログイン記録は書き換えない。

新サーバーでは `scripts/sync-origin-ranges.py` とsystemd timerで6時間ごとのIP範囲更新を有効にした。取得した公式データからNginx設定とファイアウォールを同期し、SSH設定を保持する。IPv4/IPv6不足・全世界許可・ルール超過・移行途中のポート構成では失敗する。4件の境界テストと、新サーバーで87範囲の同期・AWSからの設定再取得照合が成功。旧サーバーの8000制限の自動更新には適用していない。

`scripts/renew-origin-certificate.sh` は1日2回のtimerを有効化済み。Certbotの更新後にNginx構文検証・reloadと残存期間14日以上を確認し、失敗をjournalと既存アプリログへ記録する。証明書更新のdry-run成功。両timerの実行ファイルは `/usr/local/libexec/carbohydratepro/` にroot所有で配置した。将来スクリプトを変更した際は、この配置済みコピーも更新する。

## OS移行: 本番切り替え完了

一時的な追加費用、設定・データ移送、本番切り替え、実ログ保存についてそれぞれユーザーの承認を得て実施した。旧サーバーは2026-10-24 JSTの明示依頼で削除済み。

- 新サーバーの作成時IPv4は `13.231.169.220`。現在は固定IP `54.238.169.177` に変更済みで、作成時IPへ接続しない。
- AWSから取得した公開ホスト鍵と照合してSSH接続を検証した。専用SSH設定は `workspace/security-hardening-20261022/ssh-config`。
- OS: Amazon Linux `2023.12.20261021`、カーネル `6.1.188-233.393.amzn2023.x86_64`。`dnf upgrade` に追加更新なし。
- Docker `25.0.16`、Compose `v5.6.1`、Git、cronieを導入。Composeの公式公開SHA256とダウンロードを照合済み。
- SSHのパスワード・キーボード対話認証・rootログインを無効化し、構文と実効設定、新規SSH接続を検証。現在のLightsailルールは管理元とブラウザSSH用の22番、CloudFront範囲だけの443番。8000番は閉鎖。最終切り替え時に検証用internalネットワークを外し、本番利用を再開した。
- 1GiBのswapを用意。Dockerの標準ログは1ファイル10MB、5世代に制限。
- 現行本番コミット `8b294bd` のGit bundleから配置。未コミットのUI変更は含めていない。GitHubへの認証不要のHTTPS参照とmainの一致を確認し、新リポジトリのoriginをGitHub HTTPSへ設定した。GitHub用の秘密鍵をコピーする必要はなかった。
- 本番と同じgunicorn・cron・PostgreSQLイメージを転送し、3つのimage IDが一致することを確認。現在は新側で4サービス稼働、旧側のgunicorn・cron停止を照合済み。転送アーカイブはローカル・新サーバーとも0600で、転送前後のSHA256も一致。
- Nginx `1.30.6` の固定digestイメージを取得し、新OSで実行確認。
- 証明書更新用の公式 `certbot/dns-route53` は `5.8.0`、取得digestは `sha256:38fdfaed25f1e2554b22b835d257756afcfe3acacb8f943ec0884c251e561130`。新サーバー内で秘密鍵を生成し、2ドメインの公開証明書を取得済み。有効期限は2027-01-20 UTC。DNS-01更新dry-runとreloadまで成功した。
- IAMユーザー `carbohydratepro-origin-maintenance` と新しい専用キーを作成。DNS検証用TXT2件だけの更新と、新インスタンスだけのファイアウォール更新を許可する。個人の管理者キーは配置していない。設定は `/etc/carbohydratepro/origin-maintenance.env`、root所有0600。AWS Access Analyzerのポリシー検証で指摘0件。
- 新規のログ専用IAMユーザー `carbohydratepro-al2023-log-uploader` と専用キーを作成。S3権限は新サーバー専用prefixだけ。明示承認後に実ログ保存と毎時cronを有効化し、14:35:58 UTCに初回の正常終了を確認した。
- Composeの `CONTAINER_RESTART_POLICY=unless-stopped` を新環境で設定し、3コンテナの実効設定を照合済み。開発側の既定値は従来どおり自動再起動なし。TLS移行後の通常デプロイが公開HTTPS経由でヘルスチェックするようスクリプトも準備した（構文検証済み、通常デプロイ自体は未実施）。

### 復元・検証結果

設定・DB等の移送は、一度自動承認レビューで拒否された後、ユーザーから対象と宛先への明示承認を得て実施した。

- PostgreSQLの論理dumpを新DBへ復元し、旧DBと全40テーブルの件数・行内容ハッシュが一致した。
- Django checkとmigration差分確認が成功。トップ、ログイン、家計簿/予定/メモのデモ、CSS/JSがHTTP 200。静的ファイルの内容ハッシュも一致。
- 検証用 `migration-check.yml` と `project/settings/migration_check.py` を新サーバーだけに配置。internal Dockerネットワークの外向きTCP接続失敗、メールbackendがlocmem、DEBUG=False、cron未起動を確認した。
- 公開CAを信頼するTLS接続で、秘密値なし/誤りの403、非CloudFront接続元の403、正しい秘密値と許可元によるアプリ/静的ファイル200を確認。切り替え前は隔離ネットワークで接続元を再現し、切り替え後は実際のCloudFront通信でも配信と実IP記録を確認した。
- 転送ヘッダーの検証済みクライアントIPが記録され、秘密値がアクセスログに出ないことを確認。
- アプリ・DB再作成後にもTLS・Django・migration検証が成功。切り替え後の新本番もHTTP 200。
- 本番切り替え時には旧側の更新を止めて最新dump・media・設定を再取得し、全40テーブルと438ファイルを照合してから利用を再開した。

### 実ログ送信の承認履歴（解消済み）

新サーバーのsystem journalとアプリログを既存S3の `s3://carbohydratepro-system-logs/production/carbohydratepro-al2023-20261022/` へ保存する処理は、一度自動承認レビューで停止した。IP・メールアドレス等を含み得ることと具体的な保存先を提示し、ユーザーから明示承認を得た後に有効化した。固定文による事前検証に続き、実ログでもS3容量・SHA256・AES256を検証して成功。専用キーはroot所有0600。毎時10分に実行し、保存期間は既存運用どおり自動削除なし。

具体的な切り替え・復旧手順は `production-al2023-cutover-2026-10-22.md` を参照。

- 作成名: `carbohydratepro-al2023-20261022`
- リージョン/AZ: `ap-northeast-1` / `ap-northeast-1a`
- Blueprint: `amazon_linux_2023`（調査時の提供版 `2023.12.20261021.0`）
- Bundle: `micro_3_0`（現行と同じ1GB RAM、2 vCPU、40GB、IPv4+IPv6）
- SSHキーペア: 既存の本番用キーペア。新規作成直後は22番を管理元と `lightsail-connect` だけに限定し、Webポートは開けない。
- 費用: AWS APIで月額7 USD相当を確認。旧サーバーと並行稼働する間は追加費用が発生する。税・為替・転送量等は別。旧サーバーは停止だけでも課金が続くため、後日の削除判断を別途行う。
- 作成JSON: `workspace/security-hardening-20261022/create-al2023.json`。AWS CLIの入力検証を実施済み。初期ファイアウォールJSONも同じ場所に準備済み。

```bash
aws lightsail create-instances \
  --cli-input-json file://workspace/security-hardening-20261022/create-al2023.json \
  --region ap-northeast-1
aws lightsail put-instance-public-ports \
  --cli-input-json file://workspace/security-hardening-20261022/al2023-initial-firewall.json \
  --region ap-northeast-1
```

移行時に確認した項目:

1. 新ホスト鍵をAWS側の記録と照合し、OS・カーネル・Docker・Composeを更新する。旧ホストのrootファイルシステムを丸ごと複製しない。
2. 本番の現行コミットと今回承認した設定だけを配置する。ローカルの未完了UI変更を含めない。アプリ・PostgreSQLのイメージは現行稼働版と一致させ、OS移行に無関係な依存関係更新を混ぜない。
3. PostgreSQLの論理バックアップとmedia・必要な設定を権限付きで退避し、ハッシュを記録する。稼働中のPostgreSQLデータディレクトリをtarでコピーして復元元にしない。
4. 新サーバーの隔離DBへ復元し、テーブル件数・制約・migration状態・アプリの参照動作を検証する。cronと外部メール送信は検証中に動かさない。
5. 切り替え直前にWeb書き込みと旧cronを止め、最終バックアップ・差分ファイルを反映してから、固定IPまたはDNSを切り替える。現在のオリジンAレコードTTLは300秒。
6. 二重書き込み・定期支払いの二重実行を防ぎ、新側だけで書き込みとcronを再開する。再開後に旧側へ戻す場合は、新側のデータを保全して差分移行する。IPだけ戻して新しい書き込みを失わないようにする。
7. アプリ・静的ファイル・認証・ログ保管・証明書更新・SSH制限を確認する。旧サーバー削除とバックアップの保管期限は別途決める。

## 残る運用上の扱い

- 旧サーバーは2026-10-24 JSTに削除完了。旧インスタンスへの切り戻しは使用不可。新本番の固定IP・4サービス・公開HTTP 200を削除後に確認した。
- セキュリティ差分のコミット・push・本番のGit追跡状態の統一は完了。今後の通常デプロイでは最新mainを基準にする。
- 秘密情報を含むバックアップは引き続き非公開領域で保管。旧環境の廃止と合わせて保管期限・整理を判断する。
- OSの継続的な更新・必要な再起動の計画は運用で継続する。今回の移行時点では最新AL2023であるが、将来のOS更新を無停止で自動適用する設定にはしていない。
