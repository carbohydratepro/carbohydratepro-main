# Project Brief

## プロジェクト

- 名称: `carbohydratepro`
- ユーザー呼称: `carbohydrate-main`
- 実パス: `/home/carbohydratepro-main` on WSL `archlinux`
- 対象環境: Arch Linux / WSL2
- 作業目的: 個人向けライフ管理Webアプリの一部バグ修正および仕様変更

## プロダクト概要

家計簿、定期支払い、タスク管理、メモ、買い物リスト、習慣トラッカー、ログ監視を提供する Django ベースのWebアプリケーション。

## 作業範囲

- 既存のDjango/TypeScript構成を前提に、不具合修正と仕様変更を行う。
- 変更対象に応じて、Django単体テスト、TypeScriptビルド、Playwright E2E のいずれかを確認する。
- 本番デプロイや秘匿情報の変更は、明示依頼がある場合のみ扱う。

## 基本方針

- 既存設計、テスト構成、`CLAUDE.md` の規約を優先する。
- コンパイル済みJSは直接編集せず、`src/ts/*.ts` を編集して `npm run build` を実行する。
- ユーザーの既存未コミット変更を無断で取り消さない。
- `secret.env`、ログ、大容量生成物は必要がない限り読まない・触らない。
