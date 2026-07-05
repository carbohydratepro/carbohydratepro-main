# Active Context

## 現在の作業

`carbohydratepro` の開発環境操作、本番デプロイ、Git操作をプロジェクト共有Skillとして整備した。

## 対象リポジトリ

- WSL: `archlinux`
- パス: `/home/carbohydratepro-main`
- ブランチ: `main`
- HEAD: `fc87ed2 メモリバンクを追加`

## 現在の状態

- プロジェクト本体は `/home/carbohydratepro-main` に存在する。
- ユーザー呼称の `carbohydrate-main` と完全一致するディレクトリは見つからず、実体は `/home/carbohydratepro-main` と判断した。
- 既存の未コミット変更あり:
  - modified: `.gitignore`, `docs/TESTING.md`, `package-lock.json`, `package.json`, `task.md`
  - untracked: `docs/e2e/`, `e2e/`, `playwright.config.ts`, `test.md`
- これらはユーザーまたは既存作業の変更として扱い、無断で戻さない。
- 新規作業として `AGENTS.md` と `.agents/skills/` を作成した。
- 本番環境はLightsail上で完結し、`docker-compose-dev.yml` の使用は意図された構成。

## 次に行うこと

1. 既存のE2E関連変更と今回のSkill変更を分離して扱う。
2. ユーザーから依頼があれば、Skill関連ファイルだけを日本語メッセージでコミットする。
3. 開発環境操作時はDocker DesktopのArch Linux向けWSL integrationを確認する。

## 作業上の注意

- 変更後は `activeContext.md` と `progress.md` を更新する。
- TypeScript変更では `src/ts/` を編集し、`static/app/` はビルド出力として扱う。
- DockerやWSLコマンドは必要に応じて `wsl.exe -d archlinux -- ...` 経由で実行する。
- Gitコミットメッセージは必ず日本語にする。
