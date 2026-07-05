# Active Context

## 現在の作業

`carbohydratepro` に複数アカウント切替機能を実装した。

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

## 次に行うこと

1. 必要に応じてユーザー確認後、複数アカウント切替機能の変更を日本語メッセージでコミットする。
2. 本番反映時はmigration、mediaディレクトリ、Nginx再起動を確認する。
3. Playwrightでヘッダーのアカウントメニュー、追加、切替、解除、現在のみログアウトを追加確認する。

## 作業上の注意

- 変更後は `activeContext.md` と `progress.md` を更新する。
- TypeScript変更では `src/ts/` を編集し、`static/app/` はビルド出力として扱う。
- DockerやWSLコマンドは必要に応じて `wsl.exe -d archlinux -- ...` 経由で実行する。
- Gitコミットメッセージは必ず日本語にする。
