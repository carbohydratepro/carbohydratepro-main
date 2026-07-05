# AGENTS.md

## 適用範囲

このファイルはリポジトリ全体に適用する。
下位ディレクトリに別の `AGENTS.md` がある場合は、より近いファイルの指示を優先する。

## プロジェクト概要

CarbohydratePro は、家計簿、タスク、メモ、買い物リスト、習慣管理などを提供する個人向けライフ管理Webアプリケーションである。

## 技術構成

- Python / Django 5.2
- PostgreSQL 16
- TypeScript
- Docker / Docker Compose
- Playwright
- Ruff / Pyright / djlint

## ディレクトリ構成

- `project/`: Django設定、URL、middleware
- `auth_app/`: 認証、ユーザー、デモ機能
- `app/`: 業務機能
  - `expenses/`: 家計簿、定期支払い
  - `task/`: スケジュール、一時タスク
  - `memo/`: メモ
  - `shopping/`: 買い物リスト
  - `habit/`: 習慣管理
- `src/ts/`: TypeScriptソース
- `static/app/`: TypeScriptのコンパイル出力
- `e2e/`: Playwright E2Eテスト
- `.agents/skills/`: プロジェクト共有Skill
- `memory-bank/`: プロジェクト状況、技術情報、作業履歴

## 作業開始時

- `memory-bank/projectbrief.md`、`memory-bank/activeContext.md`、`memory-bank/progress.md` を確認する。
- `git status` を確認し、既存の未コミット変更を把握する。
- 既存変更はユーザーの作業として扱い、明示的な依頼なしに取り消さない。
- 対象機能の既存コード、テスト、類似実装を読んでから変更する。

## 基本方針

- 既存の設計、命名、責務分割、コーディングスタイルを優先する。
- 要求と無関係なリファクタリングや整形を行わない。
- 変更範囲を必要最小限に保つ。
- 挙動変更には、可能な限り対応するテストを追加または更新する。
- URL名、フォームフィールド名、テンプレート変数、API形式は互換性の一部として扱う。
- 実装上の判断や継続作業に必要な情報は `memory-bank/` に反映する。

## プロジェクト共有Skill

- 開発環境の起動、停止、再起動、ログ、Django管理操作には
  `$carbohydrate-dev-environment` を使う。
- Amazon Lightsailへの本番デプロイには
  `$carbohydrate-production-deploy` を使う。
- commit、push、pullなどのGit操作には
  `$carbohydrate-git-workflow` を使う。
- 本番環境でも `docker-compose-dev.yml` を使用する構成は意図されたものとして扱う。
- 本番デプロイはユーザーの明示依頼と実行直前の承認なしに行わない。

## セキュリティとデータ

- ユーザー所有データは、必ず認証済みユーザーで絞り込む。
- 権限、CSRF、XSS、他ユーザーのデータ分離を考慮する。
- `secret.env`、パスワード、APIキー、トークン、個人情報をコミットしない。
- ログ、バックアップ、大容量生成物を不用意に読み込んだり変更したりしない。
- 本番データ、デプロイ設定、外部サービスへ影響する操作は、明示的な依頼なしに行わない。

## Python / Django

- 機能ごとの既存構成を維持する。
  - `models.py`: データモデル
  - `forms.py`: 入力検証
  - `views.py`: HTTP処理
  - `services.py`: 更新を伴う業務処理
  - `selectors.py`: データ取得処理
- Pythonコードには可能な限り型注釈を付ける。
- 設定は `project/settings/` の適切な環境別ファイルに記述する。
- モデル変更時は新しいmigrationを作成する。
- 過去のmigrationは原則として編集しない。
- 日時処理では `USE_TZ = True` と `Asia/Tokyo` を考慮する。

## TypeScript

- フロントエンドの処理は `src/ts/*.ts` に実装する。
- `static/app/*.js` を直接編集しない。
- TypeScript変更後は `npm run build` を実行する。
- `var` を使用せず、`const` または `let` を使用する。
- `any` を避け、`unknown` から適切に型を絞り込む。
- 関数の引数と戻り値に型注釈を付ける。
- 可能な限りVanilla JavaScriptを使い、jQueryへの依存を増やさない。

## テスト

変更範囲に応じて、関連する最小単位から検証する。

### Django

```bash
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh test
```

特定機能だけを検証する場合:

```bash
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh \
  test app.tests.test_memo
```

### TypeScript

```bash
npm run build
```

### Playwright E2E

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

- テスト名には `E2E-XXX-999` 形式のケースIDを含める。
- 仕様は `docs/e2e/release-test-spec.md` と同期する。
- セレクタは `getByRole`、`getByLabel`、`getByText`、`data-testid` の順に優先する。
- 動的なDB ID、見た目だけのCSSクラス、深いDOM階層への依存を避ける。
- テストは独立させ、作成したデータを可能な限り終了時に削除する。

## 検証基準

- バックエンド変更: 関連するDjangoテスト
- TypeScript変更: `npm run build`
- UIまたは画面遷移変更: 関連するPlaywrightテスト
- モデル変更: migration確認と関連テスト
- 認証または権限変更: 未認証、通常ユーザー、他ユーザーのケース

実行できなかった検証がある場合は、理由と未確認範囲を作業結果に明記する。

## Git

- Git操作時は `$carbohydrate-git-workflow` の手順を優先する。
- ユーザーから依頼された場合のみコミットまたはpushする。
- コミットには今回の作業に関係するファイルだけを含める。
- 既存の未コミット変更を無断でステージ、コミット、破棄しない。
- コミットメッセージは必ず日本語で、変更内容が分かる簡潔な表現にする。
- コミット前に `git diff --cached` で対象を確認する。
- push前にブランチとリモートとの差分を確認する。

## ドキュメント

- 継続的な設計・環境情報は `memory-bank/` に記録する。
- 作業の区切りでは、必要に応じて `memory-bank/activeContext.md` と `memory-bank/progress.md` を更新する。
- 一時的な作業状況や個人情報を `AGENTS.md` に記載しない。
