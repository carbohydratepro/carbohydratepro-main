# Progress

## 完了

- [x] WSL `archlinux` の対象リポジトリを確認
- [x] `/home/carbohydratepro-main` を作業対象として特定
- [x] README、CLAUDE.md、主要設定、テスト手順を確認
- [x] メモリバンクの内容を実プロジェクト情報で更新
- [x] メモリバンクをWSL側リポジトリへ同期
- [x] ルート `AGENTS.md` を作成
- [x] 開発環境操作Skillを作成
- [x] 本番デプロイSkillを作成
- [x] Git操作Skillを作成
- [x] Skill構造とスクリプトを検証
- [x] README・AGENTS.md・メモリバンクをWSL側へ同期
- [x] 複数アカウント切替の要件整理
- [x] DB永続のアカウントグループ/所属モデルを追加
- [x] アカウントアイコンアップロードとメディア配信設定を追加
- [x] 既存アカウント追加、切替、解除、現在のみログアウトを実装
- [x] アカウント追加画面から新規アカウント作成を除外
- [x] アカウント切替と解除をアカウント編集画面へ統合
- [x] 現在アカウントのみのログアウト、自動切替、ログアウト済みアカウント再ログインを実装
- [x] 追加Djangoテストと基本検証を実行

## 未着手

- [ ] 複数アカウント切替のPlaywright E2E追加
- [ ] 本番反映時のmigrationとNginx/media配信確認

## 既知の状態

- `/home/carbohydratepro-main` には既存の未コミット変更がある。
- Playwright関連ファイルが既に追加・変更されている。
- READMEのPythonバージョン記載は3.12だが、`pyproject.toml` のPyright/Ruff設定は3.11系を対象にしている。
- 通常サンドボックスユーザーではWSL登録が見えないため、ホスト権限の `wsl.exe` 経由で操作する。
