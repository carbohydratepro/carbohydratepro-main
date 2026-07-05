---
name: carbohydrate-production-deploy
description: CarbohydrateProをAmazon Lightsail上の本番環境へSSH経由でデプロイし、コード更新、Dockerビルド、再起動、migration、collectstatic、静的ファイル検証、ヘルスチェックを行う。ユーザーが本番デプロイ、Lightsail反映、リリース、production更新を明示的に依頼したときに使う。
---

# CarbohydratePro本番デプロイ

本番環境はAmazon Lightsail上で完結し、意図的に `docker-compose-dev.yml` を使用する。
ファイル名を理由に別のComposeファイルへ置き換えない。

## 必須確認

1. ユーザーが本番デプロイを明示的に依頼していることを確認する。
2. 対象ホスト、ブランチ、リモートディレクトリを確認する。
3. ローカルの `git status --short --branch` と対象コミットを表示する。
4. 未コミット変更がある場合は原則停止する。続行にはユーザーの明示承認が必要。
5. 実行コマンドを提示し、実行直前に最終承認を得る。

## 実行

```bash
bash .agents/skills/carbohydrate-production-deploy/scripts/run-production-deploy.sh \
  --host user@lightsail-host \
  --branch main
```

必要な場合:

```bash
bash .agents/skills/carbohydrate-production-deploy/scripts/run-production-deploy.sh \
  --host user@lightsail-host \
  --branch main \
  --remote-dir carbohydratepro
```

`DEPLOY_HOST` を設定している場合は `--host` を省略できる。

## デプロイ内容

- リモートで `git fetch`、ブランチ切替、fast-forward pull
- `docker-compose-dev.yml` によるイメージビルド
- コンテナ停止・起動とgunicorn準備確認
- Django migrationとcollectstatic
- ローカルと本番の `static/app/*.js` ハッシュ比較
- Nginx再起動
- コンテナ状態と静的ファイルHTTP応答の確認

## 安全ルール

- このSkillを暗黙に本番実行しない。調査や説明だけの依頼ではスクリプトを実行しない。
- `main` 以外のブランチはユーザーが明示した場合だけ使う。
- force push、リモートのreset、未コミット変更の破棄を行わない。
- SSH鍵、`secret.env`、本番の秘匿値を表示しない。
- 失敗時は停止し、失敗段階とログの要点を報告する。自動ロールバックは行わない。
- 実環境へのforward testは行わない。
