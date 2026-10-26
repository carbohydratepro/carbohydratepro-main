---
name: carbohydrate-inquiry-response
description: CarbohydratePro本番に届いたお問い合わせ（ContactMessage）を確認し、要望・不具合を開発環境で実装・検証して、本番反映とステータス更新まで進めるとき。「お問い合わせに対応して」「問い合わせ一覧を見て」「要望を反映して」と言われたときに使う。
---

# CarbohydratePro お問い合わせ対応

本番のお問い合わせを読み取り、対応内容を開発環境で実装・検証し、承認を得て本番へ反映する。
本番は読み取りを既定とし、書き込み（ステータス更新・デプロイ）は必ず直前に承認を取る。

## 1. 本番のお問い合わせを読む（読み取り専用）

```bash
export INQUIRY_SSH_HOST=<ssh config の Host 別名>
export INQUIRY_SSH_CONFIG=<専用 ssh config を使う場合のみ>
S=.agents/skills/carbohydrate-inquiry-response/scripts/production-inquiries.sh
bash "$S" list                       # 未対応の一覧（--status all|in_progress|resolved, --limit N）
bash "$S" show <ID>                   # 本文と返信を全文表示
```

- 接続先・鍵・IPはスキルやリポジトリに書かない。ssh config の Host 別名で渡す。
  ホスト鍵の警告が出たら `StrictHostKeyChecking` を緩めず、検証済みの known_hosts を持つ設定を使う。
- 送信者はユーザーIDだけで扱う。メールアドレス・本文を `memory-bank/` やコミットへ転記しない
  （記録には `#ID` と件名の要約だけを残す）。
- ユーザーが件名で対象を指定した場合は、一覧から該当IDを特定して `show` で全文を読む。

## 2. 既存対応の有無を調べる

同じ要望が過去に対応済みでも、ステータスが「未対応」のまま残っていることがある。
また、後の変更で対応が戻っている（退行）ことがある。実装前に必ず確認する。

```bash
git log --oneline --since=<問い合わせ日> | grep -i <キーワード>
git log --oneline -S"<該当文言やID>" -- <対象ファイル>
```

- 対応済みのコミットがあれば、現在のコードで本当に効いているかを読んで確かめる。
- 後の意図的な変更で仕様が変わっていた場合は、どちらを優先するかを作業結果で説明する。
- 通知先・メール・外部連携など、コードではなく本番の設定値や運用で満たされうる要望は、
  実装前に「今すでにそう動いていないか」をユーザーに確認する（秘密設定は読まない）。
  例: #14「開発用アドレスにも通知」は既存設定で届いており、追加実装は不要だった。

## 3. 開発環境で実装・検証する

- 項目ごとに「実装済み／今回対応／対応しない（理由）」を切り分けてから着手する。
- プロジェクト規約（`AGENTS.md` の索引、`.claude/rules/`）に従う。新画面はデモ対応も確認する。
- 検証は `carbohydrate-dev-environment` スキルと `.agents/knowledge/testing.md` に従う。
  Django の関連テスト・全体テスト、`npm run check`、該当する Playwright E2E
  （`node scripts/test-ui-session.mjs <spec>` で一時ユーザーを使う）を実行する。
- 他ユーザーのお問い合わせが見えないこと（404・検索結果に出ない）を必ずテストする。

## 4. 本番へ反映する（承認必須）

- コミット・push は `carbohydrate-git-workflow`、反映は `carbohydrate-production-deploy` に従う。
- どちらもユーザーの明示依頼と実行直前の承認がなければ行わない。

## 5. ステータスを更新する（承認必須・本番反映後）

本番に反映して動作を確認した項目だけを更新する。対象IDと新ステータスを提示し、承認後に実行する。

```bash
bash "$S" set-status <ID> resolved --yes      # open | in_progress | resolved
```

- 一部だけ対応した問い合わせは `in_progress` にとどめる。
- 返信（メール送信を含む）は管理画面 `/carbohydratepro/manage/contacts/<ID>/` から行う。
  外部へのメール送信なので、文面を提示してユーザーの承認を得てから送る。

## 6. 報告

- 問い合わせごとに、対応内容・既に対応済みだった項目・対応しなかった項目と理由を表にする。
- 実行した検証と、実行できなかった検証（実機確認など）を明記する。
