---
name: e2e-playwright
description: Playwright の E2E テストを書く・直すとき。セレクタとケースIDの規約あり
scope: project
updated: 2026-08-31
---

# E2E テスト（Playwright）の規約

- テスト名には `E2E-XXX-999` 形式のケースIDを含める
- 仕様は `docs/e2e/release-test-spec.md` と同期する（テストだけ直して仕様を放置しない）
- セレクタは **`getByRole` > `getByLabel` > `getByText` > `data-testid`** の順に優先する
- 動的な DB ID、見た目だけの CSS クラス、深い DOM 階層に依存しない
- テストは独立させ、作成したデータは可能な限り終了時に削除する

実行コマンドは [testing](testing.md) を参照。
