---
name: security-testing
description: ZAPなどの動的セキュリティスキャンを実行・事故復旧するとき
scope: project
updated: 2026-10-27
---

# 動的セキュリティスキャン

本番環境にOWASP ZAPをかける場合は、既定で攻撃を行わないBaseline Scanだけを使う。
Full ScanやActive Scanは、原則としてローカルまたはステージングで実施する。

- 本番Baseline Scanは公式安定版 `ghcr.io/zaproxy/zaproxy:stable` を使う。
- 公開範囲の開始点は `https://carbohydratepro.com/demo/expenses/` とする。
- 本番でFull ScanやActive Scanが必要な場合は、対象・負荷・実施時間を明示し、別途承認を得る。
- 未認証Baseline Scanでは認証後画面を評価できない。認証スキャンにはZAP contextを用意し、認証情報をリポジトリやレポートへ残さない。
- 標準の全画面確認では、匿名・通常ユーザー・管理権限の3範囲を分けて対象にする。認証後画面はローカルの専用一時アカウントでスキャンし、実ユーザーや本番データを使わず、終了時にアカウントとセッションを削除する。
- **認証済み画面、とくにDjango管理サイトへZAP Spiderを使わない。** Baseline/受動スキャンでもTraditional SpiderはHTMLフォームを自動POSTし、追加・更新・削除を成立させる。全画面確認はGETだけの明示URL許可リスト（Automation Frameworkのrequestor等）で行うか、終了後に破棄・復元できる隔離DBを使う。
- 生成レポートは `workspace/zap/YYYY-MM-DD/` に置く。`workspace/` はgit管理外であり、スキャン結果を不用意にコミットしない。

本番でBaseline Scanを選ぶ理由は、能動攻撃を避けて公開面の初期評価ができるため。ただし「能動攻撃なし」は「GETのみ・データ変更なし」を意味しない。フォームを含む認証済み範囲ではSpiderを除外する。Full Scanは能動的な攻撃を含み、サービス負荷やデータ変更の可能性があるため棄却する。

## 誤更新・削除が起きた場合

- 対象DBを使うWeb・バッチサービスを停止し、元のDBボリュームを再起動・VACUUMしない。まず論理dump、監査ログ、停止状態の物理ボリュームを別々に退避してハッシュを残す。
- 論理dumpにはMVCC上の不可視タプルが含まれない。物理コピーを別ボリュームへ展開し、`autovacuum=off`・外部ポート非公開で調査する。元ボリュームへ解析ツールを接続しない。
- PostgreSQLの`archive_mode=off`では通常のPITRはできない。ただし保持WALのフルページイメージがあれば、`pg_waldump --save-fullpage`と`pageinspect`で、剪定済みの行もページ単位で復号できる場合がある。
- 最初の破壊操作を含むフルページイメージには削除対象のタプル本体が残る。復号はさらに別の使い捨てDBで行い、元の型システムから復旧データを生成する。
- 復旧手順は未加工スナップショットの複製へ先に適用し、件数検査、Django `check`、復号元との全行・全カラムハッシュ一致を確認する。元DBへの適用は別途承認を得る。
- Djangoの`on_delete=models.CASCADE`はDB制約の`ON DELETE CASCADE`とは限らない。一時ユーザーの削除は生SQLではなくDjango ORMで行い、関連オブジェクトをCollectorに処理させる。

## Lightsail・CloudFrontの本番アクセス制限

- LightsailのIPv4/IPv6ファイアウォールは別々に適用する。SSHの接続元を限定するときは、管理者IPの変更に備えて `lightsail-connect`（AWSコンソールのブラウザSSH）を復旧経路として残す。
- オリジンの許可元はAWS公式 `ip-ranges.json` の `CLOUDFRONT_ORIGIN_FACING` を使い、更新時に範囲を再取得する。CloudFront全体の許可だけでは他人のDistributionも通るため、HTTPSとDistribution固有の秘密ヘッダー検証を組み合わせる。
- LightsailにはIPv4/IPv6それぞれ60ルールの上限があり、接続元CIDRごとに消費する。8000/443両方へ全CloudFront範囲を同時登録すると上限を超え得る。移行中の443はNginx内でも元の接続相手を検証し、CloudFrontの切り替え完了後に8000を閉じて443のファイアウォール制限へ移す。
- 実クライアントIPを採用するのは信頼したCloudFront接続からのみ。Nginxの `real_ip_recursive` で確認したIPだけをDjangoへ渡し、利用者が付けた `X-Forwarded-For` をそのまま引き継がない。ログ・アプリへの秘密ヘッダー転送も避ける。
- 既存Lightsailを維持する段階では、管理用の新しいALB/NAT等を追加する案は採らない。公開範囲制限のためだけに固定費と移行範囲を増やさず、OS移行の追加インスタンス費用を別途明示する。
- このLightsailの組み込みインスタンス権限はプロバイダー側アカウントのもので、利用者側のIAMロールとして拡張しない。証明書DNS検証・自インスタンスのファイアウォール更新には専用キーをroot所有0600で置き、個人の管理者キーを配布しない。ログ保存のキーは別にし、新ホスト専用S3 prefixへ制限する。
- OS移行ではDjangoの秘密値を一律に再生成しない。セッション等への影響とOS移行の問題を切り分けるため、まず既存値で復元を検証する。HTTPS秘密鍵と運用用AWSキーは新側用に生成する。流出が疑われるキーはこの移行互換性の方針より失効・再発行を優先する。
- 非公開バックアップ取得時の `umask 077` を展開処理にも使う場合、通常の `tar -x` はstatic_rootを0700/0600にしてNginx workerの読み取りを妨げる。信頼済みアーカイブは `tar -xp` で元の権限も復元し、秘密設定だけ明示的に0600へ戻す。内容ハッシュだけでなく、実際のNginx経由でCSS/JSの200応答を確認してからメンテナンスを解除する。
- Nginxの動的なメンテナンス判定を `if (-f ...)` で行う場合、判定するworkerがマーカーへ到達できる必要がある。秘密設定用0700ディレクトリ内には置かず、秘密を含まない専用ディレクトリを読取専用でマウントし、workerユーザーでのファイル存在確認と実HTTP 503まで検証する。
- 本番へ先行適用したセキュリティ設定を後からGit管理へ統一するときは、単一ファイルのDocker bind mountがinodeを参照していることに注意する。stash等で稼働ファイルを退避・再作成する方法は避ける。反映対象コミットと既存差分の内容・実行権限が完全一致する場合に限り、ファイルとGit indexを保全し、一致したパスだけをstageして `git merge --ff-only <固定コミット>` する。対象外の差分がないこと、前後の内容・inode・コンテナID・秘密設定が不変であること、最終worktreeがcleanであることを検証する。不一致時はこの手順を使わない。

## DB認証情報の分離・変更

- PostgreSQLの初期管理者（bootstrap role）はSUPERUSERを外せない。既存アプリがこれを使っている場合は、新しい通常権限のLOGINロールへアプリを移し、初期管理者のパスワードも変更して管理用途だけに残す。
- 所有権の移行は対象アプリDBとpublic内のアプリオブジェクトに限定する。`REASSIGN OWNED`は他のDBなど共有オブジェクトにも作用するため、一括実行しない。アプリロールはmigration用の所有権を持つが、SUPERUSER・CREATEDB・CREATEROLE・REPLICATION・BYPASSRLSは持たせない。
- DB管理用envはアプリへbind mountするリポジトリの外に0600で置く。既存DBではPOSTGRES_PASSWORDのenv変更だけでSQLロールのパスワードは変わらない。SQL変更と全利用コンテナの再作成を同じメンテナンスで行う。
- PostgreSQL公式イメージの隔離検証では、初期化中の一時サーバーをreadyと誤認しないようTCPで待つ。localhostのtrust認証ではパスワード失効を検証できないため、検証用DBはhost認証を明示的にscram-sha-256へ設定する。本番の認証確認はアプリと同じネットワーク経路で行う。
