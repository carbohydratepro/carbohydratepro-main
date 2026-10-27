---
name: testing
description: テストを実行するとき、または変更後に何を検証すべきか判断するとき
scope: project
updated: 2026-10-27
---

# テストと検証基準

変更範囲に応じて、関連する最小単位から検証する。

## Django

```bash
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh test
```

特定機能だけを検証する場合:

```bash
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh \
  test app.tests.test_memo
```

## クリーンなCI環境の静的ファイル

`project.storage.ManifestStaticFilesStorageLax` はDEBUG中もハッシュ付きURLを強制する。
`manifest_strict=False` は保存先のファイル欠落を許容しないため、CIではDjangoテスト前に
`python manage.py collectstatic --noinput --settings=project.settings.test` が必要。
ローカルの既存 `static_root` はこの前処理漏れを隠す。調査時は秘密設定・生成物を含まない
Git追跡ファイルだけの一時checkoutで再現する。テスト用storageを弱める方法ではなく、
本番と同じ収集手順をCIへ加え、静的ファイルの参照も検証対象に保つ。

## TypeScript

```bash
npm run build
```

## Playwright E2E

```bash
npm run test:e2e
```

認証後テスト:

```bash
E2E_USER_EMAIL=... \
E2E_USER_PASSWORD=... \
E2E_REQUIRE_AUTH=1 \
npm run test:e2e
```

E2E の書き方の規約は [e2e-playwright](e2e-playwright.md) を参照。

## 検証基準

| 変更内容 | 必要な検証 |
|---|---|
| バックエンド | 関連する Django テスト |
| TypeScript | `npm run build` |
| UI・画面遷移 | 関連する Playwright テスト |
| モデル | migration 確認と関連テスト |
| 認証・権限 | 未認証 / 通常ユーザー / 他ユーザー の3ケース |

実行できなかった検証がある場合は、理由と未確認範囲を作業結果に明記する。
