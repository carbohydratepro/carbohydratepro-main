# Technical Context

## 環境

- WSLディストリビューション: `archlinux`
- WSLカーネル: `6.6.87.2-microsoft-standard-WSL2`
- Linuxユーザー: `carbohydratepro`
- リポジトリ: `/home/carbohydratepro-main`
- Windows側の初期作業ディレクトリ:
  `C:\Users\masas\Documents\Codex\2026-06-06\arch-linux-carbohydrate-main-1`

## 技術スタック

- Python / Django 5.2
- PostgreSQL 16
- Django REST Framework
- Gunicorn
- Nginx
- Docker / Docker Compose
- TypeScript 5.7
- Playwright
- Ruff, Pyright, djlint 設定あり

## 開発コマンド

```bash
docker-compose -f docker-compose-dev.yml build
docker-compose -f docker-compose-dev.yml up -d
docker-compose -f docker-compose-dev.yml down
docker-compose -f docker-compose-dev.yml exec gunicorn python manage.py test
```

## フロントエンドコマンド

```bash
npm run build
npm run watch
npm run test:e2e
```

E2Eの既定URLは `http://localhost:8000`。必要に応じて `E2E_BASE_URL` を指定する。

## 静的解析・整形

- `pyproject.toml` で Pyright strict, Ruff, djlint を設定。
- Ruff target は Python 3.11。README上の使用技術表は Python 3.12 と記載があるため、実行環境は作業時に確認する。
- TypeScriptは `strict: true`。

## 注意

- Codexの通常PowerShellサンドボックスユーザーからはWSL登録が見えないため、WSL操作はホスト側権限で `wsl.exe -d archlinux -- ...` を使う。
- `secret.env` は実環境の秘匿値を含む可能性があるため、必要な場合のみ慎重に扱う。
- 大きなログファイルとして `django_debug.log` が存在する。
