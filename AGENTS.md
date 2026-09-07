# AGENTS.md — CarbohydratePro

このファイルはリポジトリ全体に適用する**索引**。詳細は索引から辿って必要時に読む。
下位ディレクトリに別の `AGENTS.md` がある場合は、より近いファイルの指示を優先する。
（`CLAUDE.md` はこのファイルへの symlink。編集はこちらに対して行う）

## プロジェクト概要

家計簿、タスク、メモ、買い物リスト、習慣管理を提供する個人向けライフ管理Webアプリ。
Python / Django 5.2、PostgreSQL 16、TypeScript、Docker Compose、Playwright、
Ruff / Pyright / djlint。

## 知識の索引

<!-- 1行 = 1ノート。書式: `- [name](.agents/knowledge/name.md) — いつ読むべきか` -->

- [code-conventions](.agents/knowledge/code-conventions.md) — Python/Django または TypeScript を書くとき。ファイル責務の分割規約あり
- [testing](.agents/knowledge/testing.md) — テスト実行時、変更後に何を検証すべきか判断するとき
- [e2e-playwright](.agents/knowledge/e2e-playwright.md) — E2Eテストを書く・直すとき。セレクタとケースIDの規約あり
- [security-testing](.agents/knowledge/security-testing.md) — ZAPなどの動的セキュリティスキャンを実行・事故復旧するとき

## 2種類の記録先を混同しない

- `.agents/knowledge/` — **恒久的な知識**（規約、罠、設計判断とその理由）。上書きして育てる
- `memory-bank/` — **流動的な作業状況**（`activeContext.md`, `progress.md`）。作業の区切りで更新する

一時的な作業状況や個人情報を `AGENTS.md` に書かない。

## 作業開始時

- `git status` を確認し、既存の未コミット変更を把握する。
  既存変更はユーザーの作業として扱い、明示的な依頼なしに取り消さない
- 前回の続きに着手する場合のみ `memory-bank/activeContext.md` と `progress.md` を読む
  （常時読まない。長く、大半は今回の作業に無関係なため）
- 対象機能の既存コード、テスト、類似実装を読んでから変更する

## 基本方針

- 既存の設計、命名、責務分割、コーディングスタイルを優先する
- 要求と無関係なリファクタリングや整形を行わない。変更範囲を必要最小限に保つ
- 挙動変更には、可能な限り対応するテストを追加または更新する

## ディレクトリ

`app/` に業務機能が機能単位で入る（`expenses/` 家計簿・定期支払い、`task/` スケジュール・
一時タスク、`memo/`、`shopping/`、`habit/`）。`auth_app/` が認証・ユーザー・デモ機能、
`project/` が Django 設定・URL・middleware。フロントは `src/ts/` に書き `static/app/` へ出力する。

## セキュリティとデータ

- ユーザー所有データは、必ず認証済みユーザーで絞り込む
- 権限、CSRF、XSS、他ユーザーのデータ分離を考慮する
- `secret.env`、パスワード、APIキー、トークン、個人情報をコミットしない
- ログ、バックアップ、大容量生成物を不用意に読み込んだり変更したりしない
- 本番データ、デプロイ設定、外部サービスへ影響する操作は、明示的な依頼なしに行わない

## Skill

- 開発環境の起動・停止・再起動・ログ・Django管理操作: `$carbohydrate-dev-environment`
- Amazon Lightsail への本番デプロイ: `$carbohydrate-production-deploy`
- commit / push / pull などの Git 操作: `$carbohydrate-git-workflow`
- 本番環境でも `docker-compose-dev.yml` を使う構成は**意図されたもの**として扱う
- 本番デプロイはユーザーの明示依頼と実行直前の承認なしに行わない
- 学びを知識ベースに書き留める / 棚卸しする: `$knowledge-capture` / `$knowledge-gc`

## Git

- Git操作時は `$carbohydrate-git-workflow` の手順を優先する
- **ユーザーから依頼された場合のみ**コミットまたはpushする
- コミットには今回の作業に関係するファイルだけを含める。既存の未コミット変更を無断で触らない
- コミットメッセージは必ず日本語で、変更内容が分かる簡潔な表現にする
- コミット前に `git diff --cached`、push前にリモートとの差分を確認する
