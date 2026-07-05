---
name: carbohydrate-git-workflow
description: CarbohydrateProリポジトリで状態確認、差分確認、ステージ、コミット、pull、push、ブランチ確認などのGit操作を安全に行う。ユーザーがGit状態、コミット、push、pull、ブランチ、履歴、差分の操作を依頼したときに使う。コミットメッセージは必ず日本語にする。
---

# CarbohydratePro Git操作

## 基本手順

1. `git status --short --branch` でブランチと既存変更を確認する。
2. `git diff` と必要に応じて `git diff --cached` で内容を読む。
3. ユーザーの依頼に関係するファイルだけをステージする。
4. `git diff --cached --stat` と `git diff --cached --name-status` で混入がないか確認する。
5. 日本語のコミットメッセージでコミットする。
6. push依頼がある場合だけ、リモートとの差分を確認してpushする。

## コミットルール

- コミットメッセージは必ず日本語で記載する。
- 変更内容が分かる簡潔な命令形または体言止めを使う。
- 例:
  - `開発環境操作Skillを追加`
  - `ログイン画面のエラー表示を修正`
  - `E2Eテストの認証ケースを追加`
- `update`、`fix`、`WIP` だけの曖昧なメッセージを使わない。
- ユーザーが指定した日本語メッセージがある場合はそれを優先する。

## 安全ルール

- ユーザーの既存未コミット変更を無断でステージ、コミット、破棄しない。
- `git add .` や `git add -A` は、全変更を含める明示依頼がない限り使わない。
- commit、amend、push、pull、rebase、ブランチ削除はユーザーの依頼または明確な作業目的がある場合だけ行う。
- `git reset --hard`、`git checkout --`、`git clean -fd` を無断で使わない。
- force pushは行わない。必要な場合は理由と影響を説明し、明示承認を得る。
- push前に現在のブランチ、upstream、ahead/behindを確認する。
- コンフリクトではユーザー変更を優先し、勝手に片側を採用しない。

## 推奨コマンド

```bash
git status --short --branch
git diff -- path/to/file
git add -- path/to/file
git diff --cached --stat
git diff --cached --name-status
git commit -m "日本語のコミットメッセージ"
git fetch origin
git status --short --branch
git push origin <branch>
```

## 報告

コミットまたはpush後は、コミットハッシュ、メッセージ、対象ファイル、push先を報告する。
未コミット変更が残る場合は、それらが今回の操作に含まれていないことも明記する。
