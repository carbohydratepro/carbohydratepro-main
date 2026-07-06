# Playwright E2E テスト

このディレクトリは、リリース前確認を Playwright で自動化するための仕様と運用ルールをまとめています。

## 実行前提

- 開発サーバーは既定で `http://localhost:8000` を使います。
- URL を変える場合は `E2E_BASE_URL` を指定します。
- 認証後フローを実行する場合は、事前にテスト用ユーザーを用意して `E2E_USER_EMAIL` と `E2E_USER_PASSWORD` を指定します。
- 認証情報が未設定の場合、認証後フローは失敗します。ローカルで公開ページだけ確認したい場合に限り `E2E_ALLOW_AUTH_SKIP=1` を指定します。

## 初回セットアップ

```bash
npm install
npx playwright install chromium
```

CI と同じ前提データを手元で作る場合:

```bash
python manage.py migrate --settings=project.settings.e2e
python manage.py seed_e2e_user --email e2e@example.com --username e2e-user --password 'e2e-password-123' --reset --settings=project.settings.e2e
# アカウント切替テスト用のサブユーザー
python manage.py seed_e2e_user --email e2e-sub@example.com --username e2e-sub-user --password 'e2e-password-123' --reset --settings=project.settings.e2e
```

アカウント切替テスト（`account-switch.spec.ts`）はサブユーザーの認証情報を
`E2E_SECONDARY_USER_EMAIL` と `E2E_SECONDARY_USER_PASSWORD` で渡します。
メインとサブは互いに未連携の状態で実行してください（テスト内で連携と解除を行います）。

## Chrome DevTools MCP

Codex からブラウザを操作するため、ユーザー設定 `~/.codex/config.toml` に `chrome-devtools` MCP を追加します。この環境では通常の `google-chrome` がないため、Playwright がインストールした Chromium を `--executablePath` に指定します。

```toml
[mcp_servers.chrome-devtools]
command = "npx"
args = ["-y", "chrome-devtools-mcp@latest", "--headless", "--isolated", "--no-usage-statistics", "--executablePath", "/home/carbohydratepro/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome"]
```

MCP 設定を反映するには Codex セッションの再起動が必要です。

Docker 開発環境を使う場合:

```bash
docker-compose -f docker-compose-dev.yml up -d
```

## 実行コマンド

```bash
npm run test:e2e
npm run test:e2e:headed
npm run test:e2e:ui
npm run typecheck:e2e
npm run check
```

認証後フローも含める例:

```bash
E2E_USER_EMAIL=user@dev.local E2E_USER_PASSWORD='your-password' npm run test:e2e
```

公開ページだけをローカルで軽く確認する例:

```bash
E2E_ALLOW_AUTH_SKIP=1 npm run test:e2e -- e2e/tests/public.spec.ts
```

## 仕様との紐づけ

- リリース前の包括チェックリスト: `test.md`
- Playwright 化ルール: `docs/e2e/rules.md`
- 自動化ケースの詳細仕様: `docs/e2e/release-test-spec.md`
- テストコード: `e2e/tests/*.spec.ts`

各 Playwright テスト名には `E2E-XXX-999` のケースIDを含めます。テストコード内にも対応する md アンカーをコメントで記載します。

## 失敗時の確認

- `playwright-report/` の HTML レポートを確認します。
- 失敗時は trace、screenshot、video が `test-results/` に残ります。
- `console.error` と `pageerror` は失敗扱いです。
- `console.warn` も失敗扱いにしたい場合は `E2E_FAIL_ON_CONSOLE_WARN=1` を指定します。
