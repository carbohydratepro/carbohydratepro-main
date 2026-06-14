# System Patterns

## 全体構成

- Djangoプロジェクト: `project/`
- 認証アプリ: `auth_app/`
- 業務アプリ: `app/`
- TypeScriptソース: `src/ts/`
- 生成JS出力先: `static/app/`
- Djangoテスト: `app/tests/`, `auth_app/tests/`, `project/tests/`
- Playwright E2E: `e2e/tests/`, `e2e/fixtures/`

## Django構成

- 設定は `project/settings/base.py`, `development.py`, `production.py`, `test.py` に分割されている。
- `AUTH_USER_MODEL` は `auth_app.CustomUser`。
- DBはPostgreSQL。環境変数は `secret.env` から `django-environ` で読む。
- URLは公開・認証系を `auth_app.urls`、ログイン後機能を `/carbohydratepro/` の `app.urls` に集約する。
- 管理画面は `system-control-panel/` のカスタム `SecureAdminSite`。通常の `/admin/` は404扱い。
- middleware はメンテナンス、管理セキュリティ、メール認証、アクティビティ記録を含む。

## 業務ドメイン

`app/` 内は機能ごとに `models.py`, `forms.py`, `views.py`, `services.py`, `selectors.py` を持つ構成。

- `expenses`: 支払い方法、カテゴリ、取引、定期支払い。
- `task`: タスク、ラベル、一時タスクボード。
- `memo`: メモ、メモ種別。
- `shopping`: 買い物項目。
- `habit`: 習慣、習慣記録。
- `app/models.py` はサブドメインモデルをimportし、横断モデルとして `ActivityLog`, `ContactMessage` を定義する。

## フロントエンド

- `CLAUDE.md` に従い、フロントエンド変更は `src/ts/` のTypeScriptを編集する。
- `tsconfig.json` は `strict: true`, `module: none`, `outDir: static/app`, `rootDir: src/ts`。
- `var` と `any` は避け、関数引数・戻り値に型を付ける。
- `static/app/*.js` はビルド成果物として扱う。

## テストパターン

- Django単体テストは `python manage.py test`。
- 開発環境では `docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py test` を基本とする。
- Playwrightは `npm run test:e2e`。`E2E_BASE_URL` 既定値は `http://localhost:8000`。
- UI変更や認証後フローの変更は、必要に応じてE2Eも更新する。
