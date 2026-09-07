---
name: code-conventions
description: Python/Django または TypeScript のコードを書くとき。ファイル責務の分割規約あり
scope: project
updated: 2026-08-31
---

# コーディング規約

## Python / Django

機能ごとに、責務でファイルを分ける既存構成を維持する。

| ファイル | 責務 |
|---|---|
| `models.py` | データモデル |
| `forms.py` | 入力検証 |
| `views.py` | HTTP 処理 |
| `services.py` | **更新を伴う**業務処理 |
| `selectors.py` | **データ取得**処理 |

- Python コードには可能な限り型注釈を付ける
- 設定は `project/settings/` の適切な環境別ファイルに記述する
- モデル変更時は新しい migration を作成する。**過去の migration は原則編集しない**
- 日時処理では `USE_TZ = True` と `Asia/Tokyo` を考慮する

## TypeScript

- フロントエンドの処理は `src/ts/*.ts` に実装する
- **`static/app/*.js` を直接編集しない**（コンパイル出力。変更後は `npm run build`）
- `var` を使わず `const` / `let` を使う
- `any` を避け、`unknown` から適切に型を絞り込む
- 関数の引数と戻り値に型注釈を付ける
- 可能な限り Vanilla JavaScript を使い、jQuery への依存を増やさない

## 互換性として扱うもの

URL名、フォームフィールド名、テンプレート変数、API形式は互換性の一部。
安易に変更しない。
