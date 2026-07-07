# Active Context

## 現在の作業

`carbohydratepro` に複数アカウント切替機能を実装した。
続けてセキュリティ・パフォーマンス・デザイン統一の改善を実施した（2026-07-06）。

## 直近の改善内容（2026-07-06）

- ログイン一時ロック: 15分間に5回失敗で認証を拒否（`services.is_login_locked`、閾値は `LOGIN_LOCKOUT_THRESHOLD` / `LOGIN_LOCKOUT_WINDOW_MINUTES` で変更可）。
- `get_client_ip` は X-Forwarded-For の右端（信頼プロキシが付加した値）を使用。
- ログイン履歴の地域解決（ipapi.co）はバックグラウンドスレッド化し、ログインをブロックしない。
- DRF（rest_framework / simplejwt）は未使用のため削除。gunicorn イメージ再ビルド済み。
- ログは RotatingFileHandler（10MB×5世代）、django ロガーは INFO に変更。
- アカウント連携は親子リンク方式（`AccountGroupLink`）に変更。追加時は親→子のリンクを作成し、グループ合流はしない。切替候補は「自分＋直接の子」＋「親＋その兄弟」のファミリー範囲。孫や子の別の親は辿らない。子は複数の親に所属可能。旧仕様の同一グループ所属データは解除時に分離される。
- デザイントークン（CSS変数）を `static/app/styles.css` に定義。カードヘッダー・ボタンを統一し、認証系テンプレートのパステル色インラインスタイルを除去。`styles.css` は両 base.html で Bootstrap より後に読み込む。

## 対象リポジトリ

- WSL: `archlinux`
- パス: `/home/carbohydratepro-main`
- ブランチ: `main`
- HEAD: `28b0f93 リリース前テスト計画を追加`

## 現在の状態

- プロジェクト本体は `/home/carbohydratepro-main` に存在する。
- ユーザー呼称の `carbohydrate-main` と完全一致するディレクトリは見つからず、実体は `/home/carbohydratepro-main` と判断した。
- 既存の未コミット変更あり:
  - modified: `.gitignore`, `docs/TESTING.md`, `package-lock.json`, `package.json`, `task.md`
  - untracked: `docs/e2e/`, `e2e/`, `playwright.config.ts`, `test.md`
- これらはユーザーまたは既存作業の変更として扱い、無断で戻さない。
- 複数アカウント切替はDB永続の `AccountGroup` / `AccountMembership` と、セッション内の有効アカウント一覧で制御する。
- アカウントアイコンは `CustomUser.avatar` の `FileField` で管理し、JPEG/PNG/WebP、2MB以下に制限する。
- アップロードファイル配信用に `MEDIA_ROOT` / `MEDIA_URL`、Nginx `/media/` alias、Composeの `./media:/var/www/media` を追加した。
- `.gitignore` には既存変更の `workspace/` に加えて `media/` を追加した。
- アカウント追加画面では、新規アカウント作成は一旦提供せず、既存アカウントのログイン追加のみ対応する。
- アカウント切替と解除は `accounts/edit/` のアカウント編集画面に統合し、解除時は確認ダイアログを表示する。
- 現在アカウントをログアウトした場合は、そのアカウントだけをセッション上のログイン済み一覧から外し、残りのログイン済み連携アカウントへ自動切替する。
- ログアウト済みの連携アカウントへ切り替える場合は、対象メールアドレス入力済みのログイン画面へ遷移する。

## 新機能（2026-07-07）

- 統合ダッシュボード `/carbohydratepro/home/`（ログイン後の遷移先。今日のタスク・習慣・今月の収支・買い物・メモを集約。デモは `/demo/home/`）。
- ICSカレンダー配信 `/calendar/<token>.ics`（`CalendarToken` モデル、タスク設定画面でURL表示・コピー・再生成）。
- PWA対応（`manifest.webmanifest`、`/sw.js` はルートスコープ配信のため `templates/sw.js`、オフライン時は `/offline/`）。

## デプロイ状況（2026-07-08）

- コミット 780be2d までを本番（54.238.169.177）へデプロイ済み（ダッシュボード・ICS配信・PWA・E2E安定化・ミドルウェア修正を含む）。マイグレーション0032適用。メンテナンスモード有効→解除の手順で実施。
- デプロイ直後にルートURLが500になる障害が発生。原因は AdminSecurityMiddleware が名前なしURLパターン（url_name=None）で `'admin' in None` の TypeError を起こすこと（ADMIN_ENABLED=False の本番のみ発火、devでは再現しない）。None を空文字扱いに修正しホットフィックス済み（3e627cd）。
- AdminSecurityMiddleware の握りつぶされていた `raise Http404` を修正し管理ブロックを有効化（secure_admin は除外）。旧 /admin/ が Http404 を return していて500になる問題も修正（780be2d、ユーザー承認済み・本番反映済み）。
- Playwright E2E はスイート全60件成功。WSL(Arch)に pacman でChromium実行用ライブラリを導入済み。

## 次に行うこと

1. 必要に応じてユーザー確認後、複数アカウント切替機能の変更を日本語メッセージでコミットする。
2. 本番反映時はmigration、mediaディレクトリ、Nginx再起動を確認する。
3. Playwrightでヘッダーのアカウントメニュー、追加、切替、解除、現在のみログアウトを追加確認する。

## 作業上の注意

- 変更後は `activeContext.md` と `progress.md` を更新する。
- TypeScript変更では `src/ts/` を編集し、`static/app/` はビルド出力として扱う。
- DockerやWSLコマンドは必要に応じて `wsl.exe -d archlinux -- ...` 経由で実行する。
- Gitコミットメッセージは必ず日本語にする。
