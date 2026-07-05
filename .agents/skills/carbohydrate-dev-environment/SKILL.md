---
name: carbohydrate-dev-environment
description: CarbohydrateProのDocker Compose開発環境を起動、停止、再起動、ビルド、状態確認、ログ確認し、migration、collectstatic、Djangoテスト、コンテナシェルを実行する。ユーザーが開発環境、ローカルサーバー、コンテナ、Docker、ログ、migration、テストの操作を依頼したときに使う。
---

# CarbohydratePro開発環境

リポジトリルートで `scripts/manage-dev-environment.sh` を使用する。
本プロジェクトでは開発環境に `docker-compose-dev.yml` を使用する。

## 基本操作

```bash
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh doctor
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh start
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh stop
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh restart
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh status
```

## その他の操作

```bash
# イメージをビルド
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh build

# ビルド後に再起動
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh rebuild

# 全サービスまたは指定サービスのログ
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh logs
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh logs gunicorn

# Django管理操作
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh check
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh makemigrations
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh migrate
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh collectstatic
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh createsuperuser
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh test
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh test app.tests.test_memo
bash .agents/skills/carbohydrate-dev-environment/scripts/manage-dev-environment.sh shell
```

## 実行ルール

- 操作前に `doctor` でDocker Composeの利用可否を確認する。
- `stop`、`restart`、`rebuild` はサービス停止を伴うため、ユーザーの意図が明確な場合だけ実行する。
- 起動後は `status` を確認する。失敗時は `logs gunicorn` と `logs db` を確認する。
- TypeScript変更後は別途 `npm run build` を実行する。
- Docker Desktop経由のWSL環境では、対象ディストリビューションのWSL integrationが有効であることを確認する。
- `secret.env` の内容を出力しない。
