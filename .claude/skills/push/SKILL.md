---
name: push
description: 変更をコミットしてリモートにプッシュする
disable-model-invocation: true
allowed-tools: Bash(git *)
---

# Git プッシュ

以下の手順で変更をコミット・プッシュする。

1. `git diff` と `git status` で変更内容を確認する
2. 変更内容を把握し、日本語でコミットメッセージを作成する
3. `git add .` で全ファイルをステージングする
4. `git commit -m "コミットメッセージ"` でコミットする
5. `git push origin main` でリモートにプッシュする
6. プッシュが成功したことを確認する

## ルール

- コミットメッセージは必ず日本語で書くこと
- $ARGUMENTS にメッセージが指定されている場合はそれを使用する
- 指定がない場合は diff の内容からコミットメッセージを自動生成する
- コミットメッセージは変更の目的がわかるよう簡潔に記述すること
