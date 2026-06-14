# Active Context

## 現在の作業

`carbohydratepro` のバグ修正・仕様変更に先立ち、メモリバンクを作成・実リポジトリ情報で更新している。

## 対象リポジトリ

- WSL: `archlinux`
- パス: `/home/carbohydratepro-main`
- ブランチ: `main`
- HEAD: `9361a69 SEO対策・スケジュールバグ修正`

## 現在の状態

- プロジェクト本体は `/home/carbohydratepro-main` に存在する。
- ユーザー呼称の `carbohydrate-main` と完全一致するディレクトリは見つからず、実体は `/home/carbohydratepro-main` と判断した。
- 既存の未コミット変更あり:
  - modified: `.gitignore`, `docs/TESTING.md`, `package-lock.json`, `package.json`, `task.md`
  - untracked: `docs/e2e/`, `e2e/`, `playwright.config.ts`, `test.md`
- これらはユーザーまたは既存作業の変更として扱い、無断で戻さない。

## 次に行うこと

1. ユーザーから最初のバグ修正または仕様変更の詳細を受け取る。
2. 対象機能の既存テストとコードを読んで、最小変更で実装する。
3. 変更に応じて Djangoテスト、TypeScriptビルド、Playwright E2E を実行する。
4. 作業結果をメモリバンクへ反映する。

## 作業上の注意

- 変更後は `activeContext.md` と `progress.md` を更新する。
- TypeScript変更では `src/ts/` を編集し、`static/app/` はビルド出力として扱う。
- DockerやWSLコマンドは必要に応じて `wsl.exe -d archlinux -- ...` 経由で実行する。
