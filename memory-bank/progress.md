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

## 未着手

- [ ] バグ修正対象の確認
- [ ] 仕様変更対象の確認
- [ ] 変更実装
- [ ] 変更に応じたテスト・ビルド・E2E確認
- [ ] 最終検証

## 既知の状態

- `/home/carbohydratepro-main` には既存の未コミット変更がある。
- Playwright関連ファイルが既に追加・変更されている。
- READMEのPythonバージョン記載は3.12だが、`pyproject.toml` のPyright/Ruff設定は3.11系を対象にしている。
- 通常サンドボックスユーザーではWSL登録が見えないため、ホスト権限の `wsl.exe` 経由で操作する。
